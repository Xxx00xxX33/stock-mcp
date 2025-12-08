# src/server/domain/services/simulation_service.py
"""Simulation Service for Paper Trading.
Manages virtual accounts and executes simulated trades using Redis for state.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from src.server.domain.adapter_manager import AdapterManager
from src.server.infrastructure.connections.redis_connection import RedisConnection
from src.server.utils.logger import logger


class SimulationService:
    """Service for managing simulated trading accounts and execution."""

    def __init__(self, redis_connection: RedisConnection, adapter_manager: AdapterManager):
        self.redis = redis_connection.get_client()
        self.adapter_manager = adapter_manager
        self._fee_rate = Decimal("0.001")  # 0.1% default fee

    def _get_balance_key(self, account_id: str) -> str:
        return f"sim:account:{account_id}:balance"

    def _get_positions_key(self, account_id: str) -> str:
        return f"sim:account:{account_id}:positions"

    async def init_account(
        self, account_id: str, initial_cash: float = 100000.0, currency: str = "USD"
    ) -> Dict[str, Any]:
        """Initialize or reset a simulation account."""
        try:
            balance_key = self._get_balance_key(account_id)
            positions_key = self._get_positions_key(account_id)

            # Reset state
            await self.redis.delete(balance_key)
            await self.redis.delete(positions_key)

            # Set initial balance
            await self.redis.hset(balance_key, currency, str(initial_cash))

            logger.info(f"Initialized simulation account {account_id} with {initial_cash} {currency}")
            return {
                "account_id": account_id,
                "status": "initialized",
                "balance": {currency: initial_cash},
                "positions": {}
            }
        except Exception as e:
            logger.error(f"Failed to init account {account_id}: {e}")
            raise

    async def get_account_state(self, account_id: str) -> Dict[str, Any]:
        """Get current account balance and positions."""
        try:
            balance_key = self._get_balance_key(account_id)
            positions_key = self._get_positions_key(account_id)

            # Fetch data
            balances_raw = await self.redis.hgetall(balance_key)
            positions_raw = await self.redis.hgetall(positions_key)

            # Convert to proper types
            balances = {k: float(v) for k, v in balances_raw.items()}
            positions = {k: float(v) for k, v in positions_raw.items()}

            # Calculate total equity (requires fetching current prices, optional for speed)
            # For now, just return raw state
            return {
                "account_id": account_id,
                "balances": balances,
                "positions": positions
            }
        except Exception as e:
            logger.error(f"Failed to get account state {account_id}: {e}")
            return {"error": str(e)}

    async def execute_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute a simulated order."""
        try:
            # 1. Get Real-time Price
            if order_type == "market":
                current_price_obj = await self.adapter_manager.get_real_time_price(symbol)
                if not current_price_obj:
                    raise ValueError(f"Could not fetch price for {symbol}")
                exec_price = Decimal(str(current_price_obj.price))
            else:
                # For limit orders in simulation, we assume immediate fill if price is reasonable
                # This is a simplification. Real simulation would need an order book.
                if price is None:
                    raise ValueError("Price required for limit order")
                exec_price = Decimal(str(price))

            # Apply slippage (random or fixed, here we use simple fixed logic for now)
            # Buy: pay more, Sell: get less
            slippage = Decimal("0.0005") # 0.05%
            if side.lower() == "buy":
                final_price = exec_price * (Decimal("1") + slippage)
            else:
                final_price = exec_price * (Decimal("1") - slippage)

            qty = Decimal(str(quantity))
            notional = final_price * qty
            fee = notional * self._fee_rate
            
            # 2. Check Balance/Positions
            balance_key = self._get_balance_key(account_id)
            positions_key = self._get_positions_key(account_id)
            
            # Assume USD for simplicity, or derive from symbol (e.g. BTC-USD -> USD)
            currency = "USD" 
            
            if side.lower() == "buy":
                # Check cash
                current_cash_str = await self.redis.hget(balance_key, currency)
                current_cash = Decimal(current_cash_str) if current_cash_str else Decimal("0")
                
                total_cost = notional + fee
                if current_cash < total_cost:
                    return {
                        "status": "rejected",
                        "reason": f"Insufficient funds. Have {current_cash}, need {total_cost}"
                    }
                
                # Update State
                await self.redis.hincrbyfloat(balance_key, currency, float(-total_cost))
                await self.redis.hincrbyfloat(positions_key, symbol, float(qty))
                
            elif side.lower() == "sell":
                # Check position
                current_pos_str = await self.redis.hget(positions_key, symbol)
                current_pos = Decimal(current_pos_str) if current_pos_str else Decimal("0")
                
                if current_pos < qty:
                    return {
                        "status": "rejected",
                        "reason": f"Insufficient position. Have {current_pos}, need {qty}"
                    }
                
                # Update State
                proceeds = notional - fee
                await self.redis.hincrbyfloat(balance_key, currency, float(proceeds))
                await self.redis.hincrbyfloat(positions_key, symbol, float(-qty))
            
            else:
                return {"status": "error", "reason": f"Invalid side {side}"}

            # 3. Return Receipt
            return {
                "status": "filled",
                "account_id": account_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": float(qty),
                "price": float(final_price),
                "fee": float(fee),
                "notional": float(notional),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Execute order failed: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}
