"""
admin/telemetry.py
Admin Telemetry system to track system usage, latency, and connected clients.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# Global in-memory metric store
TELEMETRY_DATA = {
    "total_requests": 0,
    "active_websockets": 0,  # Simulated
    "endpoints": {},
    "errors": 0,
    "avg_response_time_ms": 0.0
}

class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        path = request.url.path
        TELEMETRY_DATA["total_requests"] += 1
        
        if path not in TELEMETRY_DATA["endpoints"]:
            TELEMETRY_DATA["endpoints"][path] = {"hits": 0, "avg_time_ms": 0.0}
            
        TELEMETRY_DATA["endpoints"][path]["hits"] += 1

        try:
            response = await call_next(request)
            if response.status_code >= 400:
                TELEMETRY_DATA["errors"] += 1
        except Exception as e:
            TELEMETRY_DATA["errors"] += 1
            raise e
        finally:
            process_time = (time.time() - start_time) * 1000
            
            # Update running averages
            curr_avg = TELEMETRY_DATA["avg_response_time_ms"]
            total = TELEMETRY_DATA["total_requests"]
            TELEMETRY_DATA["avg_response_time_ms"] = curr_avg + ((process_time - curr_avg) / total)
            
            e_avg = TELEMETRY_DATA["endpoints"][path]["avg_time_ms"]
            e_hits = TELEMETRY_DATA["endpoints"][path]["hits"]
            TELEMETRY_DATA["endpoints"][path]["avg_time_ms"] = e_avg + ((process_time - e_avg) / e_hits)
            
        return response

def get_telemetry_metrics():
    """Returns the current state of the global telemetry store."""
    return TELEMETRY_DATA
