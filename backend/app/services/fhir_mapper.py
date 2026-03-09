"""
FHIR Mapper Service - Convert between SQLAlchemy models and FHIR JSON
Industry standard: HL7 FHIR R4 resource transformation
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models.encounter import Encounter
from app.models.appointment import Appointment
from app.models.observation import Observation
from app.models.patient import Patient
from app.schemas.fhir import CodeableConcept, Period, Reference, Meta, Quantity, Identifier
from app.schemas.fhir.encounter import FHIREncounter
from app.schemas.fhir.appointment import FHIRAppointment
from app.schemas.fhir.observation import FHIRObservation
from app.schemas.fhir.patient import FHIRPatient, HumanName, ContactPoint, Address, PatientContact


class FHIRMapper:
    """
    Transforms SQLAlchemy models to/from FHIR JSON format
    Industry standard: Ensures FHIR R4 compliance
    """
    
    @staticmethod
    def encounter_to_fhir(encounter: Encounter, include_patient: bool = True) -> FHIREncounter:
        """
        Convert Encounter ORM model to FHIR Encounter resource
        
        Args:
            encounter: SQLAlchemy Encounter model
            include_patient: Whether to include patient details in reference
            
        Returns:
            FHIR-compliant Encounter resource
        """
        # Meta information
        meta = Meta(
            versionId=str(encounter.id),
            lastUpdated=encounter.updated_at
        )
        
        # Patient reference
        patient_display = None
        if include_patient and encounter.patient:
            patient_display = f"{encounter.patient.given_name} {encounter.patient.family_name}"
        
        subject = Reference(
            reference=f"Patient/{encounter.patient_id}",
            display=patient_display,
            type="Patient"
        )
        
        # Encounter class (mapped to CodeableConcept)
        encounter_class_map = {
            "inpatient": ("IMP", "inpatient encounter"),
            "outpatient": ("AMB", "ambulatory"),
            "ambulatory": ("AMB", "ambulatory"),
            "emergency": ("EMER", "emergency"),
            "home": ("HH", "home health"),
            "field": ("FLD", "field"),
            "virtual": ("VR", "virtual")
        }
        
        class_code, class_display = encounter_class_map.get(
            encounter.encounter_class.lower(),
            ("AMB", "ambulatory")
        )
        
        class_concept = CodeableConcept(
            code=class_code,
            display=class_display,
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode"
        )
        
    #Period
        period = None
        if encounter.period_start or encounter.period_end:
            period = Period(
                start=encounter.period_start,
                end=encounter.period_end
            )
        
        # Reason code
        reason_code = []
        if encounter.reason_code or encounter.reason_display:
            reason_code.append(
                CodeableConcept(
                    code=encounter.reason_code,
                    display=encounter.reason_display,
                    system="http://snomed.info/sct" if encounter.reason_code else None
                )
            )
        
        # Participant (provider)
        participant = []
        if encounter.provider:
            participant.append({
                "type": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "PPRF",
                        "display": "primary performer"
                    }]
                }],
                "individual": {
                    "reference": f"Practitioner/{encounter.provider_id}",
                    "display": encounter.provider.full_name
                }
            })
        
        return FHIREncounter(
            resourceType="Encounter",
            id=str(encounter.id),
            meta=meta,
            status=encounter.status,
            class_=class_concept,  # Using alias 'class_' due to Python keyword
            subject=subject,
            participant=participant if participant else None,
            period=period,
            reasonCode=reason_code if reason_code else None
        )
    
    @staticmethod
    def appointment_to_fhir(appointment: Appointment, include_patient: bool = True) -> FHIRAppointment:
        """
        Convert Appointment ORM model to FHIR Appointment resource
        
        Args:
            appointment: SQLAlchemy Appointment model
            include_patient: Whether to include patient details
            
        Returns:
            FHIR-compliant Appointment resource
        """
        # Meta information
        meta = Meta(
            versionId=str(appointment.id),
            lastUpdated=appointment.updated_at
        )
        
        # Appointment type
        appointment_type = None
        if appointment.appointment_type:
            appointment_type = CodeableConcept(
                code=appointment.appointment_type,
                display=appointment.appointment_type.replace("_", " ").title()
            )
        
        # Service category
        service_category = []
        if appointment.service_category:
            service_category.append(
                CodeableConcept(
                    code=appointment.service_category.lower().replace(" ", "-"),
                    display=appointment.service_category
                )
            )
        
        # Participants (patient + provider)
        participants = []
        
        # Patient participant
        patient_display = None
        if include_patient and appointment.patient:
            patient_display = f"{appointment.patient.given_name} {appointment.patient.family_name}"
        
        participants.append({
            "actor": {
                "reference": f"Patient/{appointment.patient_id}",
                "display": patient_display,
                "type": "Patient"
            },
            "required": "required",
            "status": "accepted" if appointment.status in ["booked", "fulfilled"] else "tentative"
        })
        
        # Provider participant
        if appointment.provider:
            participants.append({
                "actor": {
                    "reference": f"Practitioner/{appointment.provider_id}",
                    "display": appointment.provider.full_name,
                    "type": "Practitioner"
                },
                "required": "required",
                "status": "accepted" if appointment.status == "booked" else "tentative"
            })
        
        return FHIRAppointment(
            resourceType="Appointment",
            id=str(appointment.id),
            meta=meta,
            status=appointment.status,
            appointmentType=appointment_type,
            serviceCategory=service_category if service_category else None,
            start=appointment.start_datetime,
            end=appointment.end_datetime,
            minutesDuration=appointment.duration_minutes,
            participant=participants,
            comment=appointment.comment
        )
    
    @staticmethod
    def observation_to_fhir(observation: Observation, include_patient: bool = True) -> FHIRObservation:
        """
        Convert Observation ORM model to FHIR Observation resource
        
        Args:
            observation: SQLAlchemy Observation model
            include_patient: Whether to include patient details
            
        Returns:
            FHIR-compliant Observation resource
        """
        # Meta information
        meta = Meta(
            versionId=str(observation.id),
            lastUpdated=observation.updated_at
        )
        
        # Category
        category = []
        if observation.category:
            category.append(
                CodeableConcept(
                    code=observation.category,
                    display=observation.category.replace("-", " ").title(),
                    system="http://terminology.hl7.org/CodeSystem/observation-category"
                )
            )
        
        # Code (what was observed)
        code = CodeableConcept(
            code=observation.code,
            display=observation.display,
            system="http://loinc.org"  # LOINC is standard for observations
        )
        
        # Subject (patient)
        patient_display = None
        if include_patient and observation.patient:
            patient_display = f"{observation.patient.given_name} {observation.patient.family_name}"
        
        subject = Reference(
            reference=f"Patient/{observation.patient_id}",
            display=patient_display,
            type="Patient"
        )
        
        # Encounter reference (if applicable)
        encounter_ref = None
        if observation.encounter_id:
            encounter_ref = Reference(
                reference=f"Encounter/{observation.encounter_id}",
                type="Encounter"
            )
        
        # Value (quantity or string)
        value_quantity = None
        value_string = None
        
        if observation.value_quantity is not None:
            value_quantity = Quantity(
                value=float(observation.value_quantity),
                unit=observation.value_unit or "",
                system="http://unitsofmeasure.org"
            )
        elif observation.value_string:
            value_string = observation.value_string
        
        # Interpretation
        interpretation = []
        if observation.interpretation:
            interp_map = {
                "normal": ("N", "Normal"),
                "high": ("H", "High"),
                "low": ("L", "Low"),
                "critical": ("C", "Critical"),
                "abnormal": ("A", "Abnormal")
            }
            code, display = interp_map.get(observation.interpretation.lower(), ("N", "Normal"))
            interpretation.append(
                CodeableConcept(
                    code=code,
                    display=display,
                    system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
                )
            )
        
        # Reference range
        reference_range = []
        if observation.reference_range_low is not None or observation.reference_range_high is not None:
            range_dict = {}
            if observation.reference_range_low is not None:
                range_dict["low"] = {
                    "value": float(observation.reference_range_low),
                    "unit": observation.value_unit or ""
                }
            if observation.reference_range_high is not None:
                range_dict["high"] = {
                    "value": float(observation.reference_range_high),
                    "unit": observation.value_unit or ""
                }
            reference_range.append(range_dict)
        
        # Notes
        note = []
        if observation.notes:
            note.append({
                "text": observation.notes
            })
        
        return FHIRObservation(
            resourceType="Observation",
            id=str(observation.id),
            meta=meta,
            status=observation.status,
            category=category if category else None,
            code=code,
            subject=subject,
            encounter=encounter_ref,
            effectiveDateTime=observation.effective_datetime,
            issued=observation.issued,
            valueQuantity=value_quantity,
            valueString=value_string,
            interpretation=interpretation if interpretation else None,
            note=note if note else None,
            referenceRange=reference_range if reference_range else None
        )
    
    @staticmethod
    def patient_to_fhir(patient: Patient) -> FHIRPatient:
        """
        Convert Patient ORM model to FHIR Patient resource
        
        Args:
            patient: SQLAlchemy Patient model
            
        Returns:
            FHIR-compliant Patient resource
        """
        # Meta information
        meta = Meta(
            versionId=str(patient.id),
            lastUpdated=patient.updated_at
        )
        
        # Identifiers (MRN)
        identifiers = [
            Identifier(
                system="http://hospital.example.org/mrn",
                value=patient.mrn
            )
        ]
        
        # Add insurance policy number if available
        if patient.insurance_policy_number:
            identifiers.append(
                Identifier(
                    system="http://hospital.example.org/insurance-policy",
                    value=patient.insurance_policy_number
                )
            )
        
        # Human name
        names = [
            HumanName(
                use="official",
                family=patient.family_name,
                given=[patient.given_name],
                text=f"{patient.given_name} {patient.family_name}"
            )
        ]
        
        # Contact points (telecom)
        telecom = []
        if patient.phone:
            telecom.append(
                ContactPoint(
                    system="phone",
                    value=patient.phone,
                    use="home"
                )
            )
        if patient.email:
            telecom.append(
                ContactPoint(
                    system="email",
                    value=patient.email,
                    use="home"
                )
            )
        
        # Address
        addresses = []
        if patient.address_line1:
            address_lines = [patient.address_line1]
            if patient.address_line2:
                address_lines.append(patient.address_line2)
            
            addresses.append(
                Address(
                    use="home",
                    type="physical",
                    line=address_lines,
                    city=patient.city,
                    state=patient.state,
                    postalCode=patient.postal_code,
                    country=patient.country
                )
            )
        
        # Emergency contact
        contacts = []
        if patient.emergency_contact_name and patient.emergency_contact_phone:
            # Relationship
            relationship = [
                CodeableConcept(
                    coding=[{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                        "code": "C",
                        "display": patient.emergency_contact_relationship or "Emergency Contact"
                    }]
                )
            ]
            
            contacts.append(
                PatientContact(
                    relationship=relationship,
                    name=HumanName(text=patient.emergency_contact_name),
                    telecom=[
                        ContactPoint(
                            system="phone",
                            value=patient.emergency_contact_phone
                        )
                    ]
                )
            )
        
        return FHIRPatient(
            resourceType="Patient",
            id=str(patient.id),
            meta=meta,
            identifier=identifiers,
            active=not patient.is_deleted,
            name=names,
            telecom=telecom if telecom else None,
            gender=patient.gender,
            birthDate=patient.date_of_birth.isoformat(),
            address=addresses if addresses else None,
            contact=contacts if contacts else None
        )
