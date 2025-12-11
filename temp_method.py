    def _keyword_routing(self, query: str) -> Optional[AgentRouting]:
        """Fast keyword-based routing - no API costs"""
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for rule in self.keyword_rules:
            # Check if any keyword from the rule appears in the query
            if any(keyword in query_lower for keyword in rule.keywords):
                # Use confidence directly if any keyword matches
                score = rule.confidence
                if score > best_score:
                    best_score = score
                    best_match = rule

        if best_match:
            return AgentRouting(
                agent=best_match.agent,
                confidence=best_score,
                reasoning=best_match.reasoning,
                parameters=best_match.parameters
            )

        return None
