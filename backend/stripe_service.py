import stripe
import os
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

class StripeService:
    """Handle all Stripe payment operations"""
    
    PLANS = {
        "free": {
            "price": 0,
            "monthly_tasks": 10,
            "description": "Free tier"
        },
        "starter": {
            "price": 49,
            "monthly_tasks": 500,
            "stripe_price_id": "price_1234567890",  # Create in Stripe dashboard
            "description": "Starter - €49/month"
        },
        "professional": {
            "price": 199,
            "monthly_tasks": 50000,
            "stripe_price_id": "price_0987654321",  # Create in Stripe dashboard
            "description": "Professional - €199/month"
        },
        "enterprise": {
            "price": 999,
            "monthly_tasks": 1000000,
            "stripe_price_id": "price_1111111111",  # Create in Stripe dashboard
            "description": "Enterprise - €999/month"
        }
    }

    @staticmethod
    async def create_checkout_session(user_id: str, plan: str, email: str) -> Dict:
        """Create Stripe checkout session"""
        if plan not in StripeService.PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        if plan == "free":
            return {"status": "success", "plan": "free", "message": "Free tier activated"}
        
        plan_data = StripeService.PLANS[plan]
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": plan_data["stripe_price_id"],
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                customer_email=email,
                success_url="https://yourdomain.com/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://yourdomain.com/cancel",
                metadata={"user_id": user_id, "plan": plan}
            )
            
            return {
                "status": "success",
                "checkout_url": session.url,
                "session_id": session.id
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    @staticmethod
    async def check_subscription_status(user_id: str) -> Dict:
        """Check if user has active subscription"""
        try:
            subscriptions = stripe.Subscription.list(
                limit=1,
                status="active"
            )
            
            for sub in subscriptions.data:
                if sub.metadata.get("user_id") == user_id:
                    plan_name = sub.metadata.get("plan", "unknown")
                    return {
                        "has_subscription": True,
                        "plan": plan_name,
                        "subscription_id": sub.id,
                        "current_period_end": sub.current_period_end
                    }
            
            return {"has_subscription": False, "plan": "free"}
        except:
            return {"has_subscription": False, "plan": "free"}

    @staticmethod
    async def handle_webhook(event: Dict) -> Dict:
        """Handle Stripe webhook events"""
        event_type = event["type"]
        
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            plan = session["metadata"]["plan"]
            
            return {
                "status": "success",
                "user_id": user_id,
                "plan": plan,
                "action": "activate_subscription"
            }
        
        elif event_type == "customer.subscription.deleted":
            # Handle cancellation
            return {"status": "success", "action": "deactivate_subscription"}
        
        return {"status": "received"}