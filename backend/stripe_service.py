import stripe
from fastapi import HTTPException
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeService:
    @staticmethod
    async def create_subscription(user_id: str, plan: str) -> dict:
        """Create Stripe subscription"""
        prices = {
            "starter": "price_starter_99",      # €99/mo
            "professional": "price_pro_199",    # €199/mo
            "enterprise": "price_ent_999"       # €999/mo
        }
        
        try:
            subscription = stripe.Subscription.create(
                customer=user_id,
                items=[{"price": prices.get(plan)}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            return {
                "status": "success",
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def check_subscription(user_id: str) -> dict:
        """Check if user has active subscription"""
        try:
            subscriptions = stripe.Subscription.list(
                customer=user_id,
                status="active"
            )
            if subscriptions.data:
                sub = subscriptions.data
                plan = sub.items.data.price.nickname
                return {"has_subscription": True, "plan": plan}
            return {"has_subscription": False}
        except:
            return {"has_subscription": False}