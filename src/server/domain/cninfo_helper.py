# src/server/utils/cninfo_helper.py
"""CNINFO API helper functions for A-share filings.

Based on valuecell implementation for fetching real A-share filing data
from CNINFO (巨潮资讯网).
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


def _normalize_stock_code(stock_code: str) -> str:
    """Normalize stock code to 6-digit format.

    Extracts the numeric stock code from various input formats.
    CNINFO API only requires the 6-digit code without exchange prefix.

    Args:
        stock_code: Stock code in various formats
            - "600519" (already normalized)
            - "SSE:600519" (with exchange prefix)
            - "0600519" (with extra digits)

    Returns:
        Normalized 6-digit stock code (e.g., "600519")

    Examples:
        >>> _normalize_stock_code("SSE:600519")
        "600519"
        >>> _normalize_stock_code("600519")
        "600519"
        >>> _normalize_stock_code("000001")
        "000001"
    """
    # If has exchange prefix, extract code part
    if ":" in stock_code:
        stock_code = stock_code.split(":")[-1]

    # Remove non-digit characters
    code = re.sub(r"[^\d]", "", stock_code)

    # Ensure it's a 6-digit number
    if len(code) == 6:
        return code
    elif len(code) < 6:
        return code.zfill(6)  # Pad with zeros
    else:
        return code[:6]  # Truncate to 6 digits


def _extract_quarter_from_title(title: str) -> Optional[int]:
    """Extract quarter number from announcement title.

    Args:
        title: Announcement title string

    Returns:
        Quarter number (1-4) if found, None otherwise
    """
    if not title:
        return None

    # Common patterns for quarterly reports in Chinese titles
    quarter_patterns = [
        (r"第一季度|一季度|1季度|Q1", 1),
        (r"第二季度|二季度|2季度|Q2|半年度|中期", 2),
        (r"第三季度|三季度|3季度|Q3", 3),
        (r"第四季度|四季度|4季度|Q4|年度报告|年报", 4),
    ]

    for pattern, quarter in quarter_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return quarter

    return None


async def _get_correct_orgid(
    stock_code: str, session: aiohttp.ClientSession
) -> Optional[str]:
    """Get correct orgId for a stock code from CNINFO search API.

    Args:
        stock_code: Stock code (e.g., "002460")
        session: aiohttp session

    Returns:
        Optional[str]: The correct orgId, or None if not found
    """
    search_url = "http://www.cninfo.com.cn/new/information/topSearch/query"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "www.cninfo.com.cn",
        "Origin": "http://www.cninfo.com.cn",
        "Referer": (
            "http://www.cninfo.com.cn/new/commonUrl/"
            "pageOfSearch?url=disclosure/list/search&lastPage=index"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }

    search_data = {"keyWord": stock_code}

    try:
        async with session.post(
            search_url, headers=headers, data=search_data
        ) as response:
            if response.status == 200:
                result = await response.json()

                if result and len(result) > 0:
                    # Find the exact match for the stock code
                    for company_info in result:
                        if company_info.get("code") == stock_code:
                            return company_info.get("orgId")

                    # If no exact match, return the first result's orgId
                    return result[0].get("orgId")

    except Exception as e:
        print(f"Error getting orgId for {stock_code}: {e}")

    return None


async def _fetch_announcement_content(
    session: aiohttp.ClientSession, filing_info: dict
) -> str:
    """Fetch PDF URL from CNINFO API.

    Args:
        session: aiohttp session
        filing_info: Filing information dictionary

    Returns:
        PDF URL string, or empty string if not available
    """
    try:
        # CNINFO announcement detail API
        detail_url = "http://www.cninfo.com.cn/new/announcement/bulletin_detail"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        }

        params = {
            "announceId": filing_info.get("announcement_id", ""),
            "flag": "true",
            "announceTime": filing_info.get("filing_date", ""),
        }

        async with session.post(detail_url, headers=headers, params=params) as response:
            if response.status == 200:
                result = await response.json()

                # Extract PDF link with fallback options
                pdf_url = result.get("fileUrl", "")
                if not pdf_url:
                    # Fallback: construct URL from adjunctUrl
                    announcement_data = result.get("announcement", {})
                    adjunct_url = announcement_data.get("adjunctUrl", "")
                    if adjunct_url:
                        pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"

                return pdf_url

    except Exception as e:
        print(f"Error fetching announcement details: {e}")

    # Return empty string if failed
    return ""


async def fetch_cninfo_data(
    stock_code: str,
    report_types: List[str],
    years: List[int],
    quarters: List[int],
    limit: int,
) -> List[Dict[str, Any]]:
    """Fetch real A-share filing data from CNINFO API.

    Args:
        stock_code: Normalized stock code
        report_types: List of report types
        years: List of years
        quarters: List of quarters (1-4), empty list means all quarters
        limit: Maximum number of records to fetch

    Returns:
        List[dict]: List of filing data
    """
    # CNINFO API configuration
    base_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

    # Request headers configuration
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "www.cninfo.com.cn",
        "Origin": "http://www.cninfo.com.cn",
        "Referer": (
            "http://www.cninfo.com.cn/new/commonUrl/"
            "pageOfSearch?url=disclosure/list/search&lastPage=index"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }

    # Report type mapping (supports both English and Chinese)
    category_mapping = {
        "annual": "category_ndbg_szsh",
        "semi-annual": "category_bndbg_szsh",
        "quarterly": "category_sjdbg_szsh",
    }

    # Determine exchange
    column = "szse" if stock_code.startswith(("000", "002", "300")) else "sse"

    filings_data = []
    current_year = datetime.now().year
    target_years = (
        years if years else [current_year, current_year - 1, current_year - 2]
    )

    async with aiohttp.ClientSession() as session:
        # Get correct orgId first
        org_id = await _get_correct_orgid(stock_code, session)
        if not org_id:
            print(f"Warning: Could not get orgId for stock {stock_code}")
            return []

        # Determine plate based on stock code
        plate = "sz" if stock_code.startswith(("000", "002", "300")) else "sh"

        for report_type in report_types:
            if len(filings_data) >= limit:
                break

            category = category_mapping.get(report_type, "category_ndbg_szsh")

            # Build time range
            for target_year in target_years:
                if len(filings_data) >= limit:
                    break

                # Set search time range
                start_date = f"{target_year}-01-01"
                end_date = f"{target_year + 1}-01-01"
                se_date = f"{start_date}~{end_date}"

                form_data = {
                    "pageNum": "1",
                    "pageSize": "30",
                    "column": column,
                    "tabName": "fulltext",
                    "plate": plate,
                    "stock": f"{stock_code},{org_id}",
                    "searchkey": "",
                    "secid": "",
                    "category": f"{category};",
                    "trade": "",
                    "seDate": se_date,
                    "sortName": "",
                    "sortType": "",
                    "isHLtitle": "true",
                }

                try:
                    async with session.post(
                        base_url, headers=headers, data=form_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            announcements = result.get("announcements", [])

                            if announcements is None:
                                continue

                            for announcement in announcements:
                                if len(filings_data) >= limit:
                                    break

                                announcement_title = announcement.get(
                                    "announcementTitle", ""
                                )

                                # Apply quarter filtering for quarterly reports
                                if report_type == "quarterly" and quarters:
                                    # Extract quarter from announcement title
                                    quarter_from_title = _extract_quarter_from_title(
                                        announcement_title
                                    )
                                    if (
                                        quarter_from_title
                                        and quarter_from_title not in quarters
                                    ):
                                        continue

                                # Extract filing information
                                adjunct_url = announcement.get("adjunctUrl", "")
                                filing_date = (
                                    adjunct_url[10:20]
                                    if adjunct_url
                                    else f"{target_year}-04-30"
                                )

                                filing_info = {
                                    "stock_code": announcement.get(
                                        "secCode", stock_code
                                    ),
                                    "company": announcement.get("secName", ""),
                                    "market": "SZSE" if column == "szse" else "SSE",
                                    "doc_type": report_type,
                                    "period_of_report": f"{target_year}",
                                    "filing_date": filing_date,
                                    "announcement_id": announcement.get(
                                        "announcementId", ""
                                    ),
                                    "announcement_title": announcement_title,
                                    "org_id": announcement.get("orgId", ""),
                                    "content": "",
                                }

                                # Fetch PDF URL
                                pdf_url = await _fetch_announcement_content(
                                    session, filing_info
                                )
                                filing_info["pdf_url"] = pdf_url

                                filings_data.append(filing_info)

                except Exception as e:
                    print(
                        f"Error fetching {stock_code} "
                        f"{report_type} {target_year} data: {e}"
                    )
                    continue

    return filings_data
