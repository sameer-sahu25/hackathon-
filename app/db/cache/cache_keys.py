import hashlib
from typing import List


# TTL Constants in seconds
RAG_CHUNKS_TTL = 21600         # 6 hours
ACTION_PLAN_TTL = 3600         # 1 hour
RIGHTS_CARD_TTL = 86400        # 24 hours
CHECKLIST_TTL = 43200          # 12 hours
EMBEDDING_TTL = 604800         # 7 days
USER_SESSION_TTL = 86400       # 24 hours
RESOURCES_STATE_TTL = 3600     # 1 hour
RESOURCES_NEARBY_TTL = 1800    # 30 minutes
RATE_LIMIT_TTL = 900           # 15 minutes
DAILY_STATS_TTL = 3600         # 1 hour
IMPACT_METRICS_TTL = 300       # 5 minutes


class CacheKeys:
    # AI Response Cache
    RAG_CHUNKS = "rag:{state}:{situation}:{county_hash}"
    ACTION_PLAN = "plan:{state}:{situation}:{income_bracket}:{days_bracket}"
    RIGHTS_CARD = "rights:{state}:{language}"
    CHECKLIST = "checklist:{state}:{situation}"
    EMBEDDING = "embed:{text_hash}"

    # User Session Cache
    USER_SESSION = "session:{session_token}"
    USER_INTAKE = "intake:{user_id}:latest"
    USER_PLAN = "plan:{user_id}:latest"

    # Resource Cache
    RESOURCES_STATE = "resources:{state}:{type}"
    RESOURCES_NEARBY = "nearby:{lat_rounded}:{lng_rounded}:{type}"
    HUD_PROGRAMS = "hud:{state}:{county}"

    # Rate Limiting
    RATE_LIMIT_IP = "ratelimit:ip:{ip}:{endpoint}"
    RATE_LIMIT_USER = "ratelimit:user:{user_id}:{endpoint}"

    # Analytics
    DAILY_STATS = "stats:daily:{date}"
    IMPACT_METRICS = "stats:impact"

    @staticmethod
    def make_key(*parts: str) -> str:
        key = ":".join(parts)
        if len(key) > 100:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"cache:long:{key_hash}"
        return key
