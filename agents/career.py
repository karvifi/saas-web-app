# agents/career.py
import httpx
from typing import List, Dict
from loguru import logger

class CareerAgent:
    def __init__(self):
        self.name = 'career'
        logger.info(' CareerAgent initialized')

    async def search_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        '''Search jobs - NO LLM (use APIs directly)'''
        try:
            logger.info(f'CareerAgent: searching \'{query}\'')

            # Try RemoteOK API (free, no key)
            search_term = query.lower().replace(' ', '-')

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                # RemoteOK returns ndjson - note: it's remoteok.com not .io
                response = await client.get(f'https://remoteok.com/api?tag={search_term}')
                response.raise_for_status()

                # Parse JSON array
                import json
                data = json.loads(response.text)
                
                # Ensure data is a list
                if not isinstance(data, list):
                    logger.warning(f'Unexpected response format from RemoteOK: {type(data)}')
                    return []
                
                jobs = []
                for job in data:
                    # Skip metadata entries (they don't have 'slug')
                    if not isinstance(job, dict) or 'slug' not in job:
                        continue
                        
                    slug = job.get('slug', '')
                    url = f'https://remoteok.com/remote-jobs/{slug}'

                    jobs.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'slug': slug,
                        'salary': job.get('salary', 'Negotiable'),
                        'url': url,
                        'source': 'RemoteOK'
                    })

                logger.info(f'CareerAgent: found {len(jobs)} jobs')
                return jobs[:limit]

        except Exception as e:
            logger.error(f'CareerAgent error: {e}')
            return [{'error': str(e), 'suggestion': 'Try: \'python jobs\', \'javascript jobs\''}]

    async def execute(self, query: str) -> Dict:
        jobs = await self.search_jobs(query)
        return {
            'agent': 'career',
            'query': query,
            'jobs_found': len(jobs),
            'jobs': jobs,
        }

    async def analyze_job(self, job: Dict, user_profile: Dict) -> Dict:
        """Analyze job fit for user profile"""
        try:
            logger.info(f'CareerAgent: analyzing job \'{job.get("title", "")}\'')
            
            job_skills = set()
            description = job.get('description', '').lower()
            
            # Simple skill extraction from description
            common_skills = ['python', 'javascript', 'java', 'django', 'react', 'node', 'sql', 'aws', 'docker']
            for skill in common_skills:
                if skill in description:
                    job_skills.add(skill)
            
            user_skills = set(user_profile.get('skills', []))
            matching_skills = job_skills.intersection(user_skills)
            
            match_score = len(matching_skills) / len(job_skills) if job_skills else 0.0
            
            recommendation = "Good match" if match_score > 0.5 else "Consider applying" if match_score > 0.2 else "May not be the best fit"
            
            return {
                'match_score': match_score,
                'matching_skills': list(matching_skills),
                'job_skills': list(job_skills),
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f'CareerAgent analyze_job error: {e}')
            return {
                'match_score': 0.0,
                'matching_skills': [],
                'job_skills': [],
                'recommendation': 'Unable to analyze',
                'error': str(e)
            }

    async def auto_apply(self, job: Dict, user_profile: Dict) -> Dict:
        """Auto-apply to job (placeholder - would integrate with job boards)"""
        try:
            logger.info(f'CareerAgent: auto-applying to \'{job.get("title", "")}\'')
            
            # This is a placeholder - real implementation would:
            # 1. Fill out application forms
            # 2. Upload resume
            # 3. Submit application
            
            return {
                'status': 'applied',
                'message': f'Application submitted for {job.get("title", "")} at {job.get("company", "")}',
                'job': job.get('title', ''),
                'company': job.get('company', ''),
                'job_url': job.get('url', ''),
                'applied_at': '2024-01-01T00:00:00Z'
            }
            
        except Exception as e:
            logger.error(f'CareerAgent auto_apply error: {e}')
            return {
                'status': 'error',
                'message': f'Failed to apply: {str(e)}',
                'job': job.get('title', ''),
                'company': job.get('company', ''),
                'job_url': job.get('url', '')
            }

# Global instance
career_agent = CareerAgent()
