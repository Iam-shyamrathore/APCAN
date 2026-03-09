"""FHIR routers package"""

from app.routers.fhir import encounter, appointment, observation, patient

__all__ = ["encounter", "appointment", "observation", "patient"]
