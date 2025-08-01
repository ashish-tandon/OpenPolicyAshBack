package openpolicy.api_access

import future.keywords.if
import future.keywords.in

# Rate limiting policy
allow_request if {
    input.user.authenticated
    input.requests_per_hour < user_rate_limit
}

allow_request if {
    not input.user.authenticated
    input.requests_per_hour < anonymous_rate_limit
}

# Rate limits based on user type
user_rate_limit := 10000 if {
    input.user.role == "admin"
} else := 5000 if {
    input.user.role in ["researcher", "journalist"]
} else := 2000 if {
    input.user.role == "government"
} else := 1000

anonymous_rate_limit := 1000

# API key validation
valid_api_key if {
    input.api_key
    input.api_key in valid_keys
}

# This would be populated from a database in real implementation
valid_keys := [
    "dev-key-12345",
    "prod-key-67890",
    "research-key-abc123",
    "government-key-xyz789"
]

# Federal priority data access
allow_federal_priority_data if {
    input.user.role in authorized_roles
}

allow_federal_priority_data if {
    input.user.authenticated
    input.user.verified_researcher
}

allow_federal_priority_data if {
    input.user.api_key_type == "government"
}

authorized_roles := ["researcher", "journalist", "admin", "government"]

# Data export permissions
allow_bulk_export if {
    input.user.authenticated
    input.user.role in ["admin", "researcher"]
    input.export_size < max_export_size
}

allow_bulk_export if {
    input.user.authenticated
    input.user.role == "government"
    input.export_size < government_export_limit
}

max_export_size := 10000  # Maximum records per export for researchers
government_export_limit := 50000  # Higher limit for government users

# Endpoint-specific access control
allow_endpoint_access if {
    input.endpoint == "/api/bills"
    # Public endpoint - basic rate limiting only
}

allow_endpoint_access if {
    input.endpoint == "/api/representatives" 
    # Public endpoint - basic rate limiting only
}

allow_endpoint_access if {
    input.endpoint == "/api/jurisdictions"
    # Public endpoint - basic rate limiting only
}

allow_endpoint_access if {
    startswith(input.endpoint, "/api/federal/")
    allow_federal_priority_data
}

allow_endpoint_access if {
    startswith(input.endpoint, "/api/admin/")
    input.user.role == "admin"
}

allow_endpoint_access if {
    input.endpoint == "/api/export"
    allow_bulk_export
}

allow_endpoint_access if {
    startswith(input.endpoint, "/api/parliamentary/")
    input.user.authenticated
    input.user.role in ["researcher", "journalist", "admin", "government"]
}

# Quality check access (new parliamentary features)
allow_quality_checks if {
    input.user.authenticated
    input.user.role in ["admin", "researcher"]
}

allow_quality_checks if {
    input.user.api_key_type == "government"
}

# Method-specific restrictions
allow_method if {
    input.method == "GET"
    # GET requests generally allowed (subject to other policies)
}

allow_method if {
    input.method == "POST"
    input.user.authenticated
    input.user.role in ["admin", "researcher", "government"]
}

allow_method if {
    input.method in ["PUT", "PATCH", "DELETE"]
    input.user.role == "admin"
}

# Time-based access control
allow_time_based_access if {
    # Always allow for now - could implement business hours restrictions
    true
}

# Geographic restrictions (if needed)
allow_geographic_access if {
    # Allow Canadian IPs priority access
    input.country_code == "CA"
}

allow_geographic_access if {
    # Allow other countries with authenticated access
    input.user.authenticated
}

allow_geographic_access if {
    # Research and government access from anywhere
    input.user.role in ["researcher", "government", "admin"]
}

# Content filtering based on user type
allow_sensitive_data if {
    input.user.role in ["admin", "government"]
}

allow_sensitive_data if {
    input.user.role == "researcher"
    input.user.verified_researcher
}

# Audit logging requirements
require_audit_log if {
    input.user.role == "admin"
    input.method in ["POST", "PUT", "PATCH", "DELETE"]
}

require_audit_log if {
    startswith(input.endpoint, "/api/federal/")
    input.user.authenticated
}

require_audit_log if {
    input.endpoint == "/api/export"
    input.export_size > 1000
}

# Comprehensive access decision
access_decision := {
    "allowed": allow_final,
    "rate_limit_status": rate_limit_decision,
    "audit_required": require_audit_log,
    "restrictions": access_restrictions
}

allow_final if {
    allow_request
    allow_endpoint_access
    allow_method
    allow_time_based_access
    allow_geographic_access
}

rate_limit_decision := {
    "allowed": allow_request,
    "limit": current_rate_limit,
    "remaining": current_rate_limit - input.requests_per_hour
} if {
    allow_request
}

rate_limit_decision := {
    "allowed": false,
    "limit": current_rate_limit,
    "remaining": 0,
    "retry_after": 3600  # 1 hour
} if {
    not allow_request
}

current_rate_limit := user_rate_limit if {
    input.user.authenticated
} else := anonymous_rate_limit

access_restrictions := restrictions if {
    allow_final
    restrictions := [restriction | 
        restriction := "sensitive_data_filtered" if not allow_sensitive_data
        restriction := "export_limited" if not allow_bulk_export
        restriction := "federal_data_restricted" if not allow_federal_priority_data
    ]
}

# Emergency access override (for system maintenance, etc.)
emergency_override if {
    input.emergency_mode
    input.admin_override_key == "emergency-override-2024"
    input.user.role == "admin"
}

allow_final if {
    emergency_override
}

# Special provisions for Canadian government access
government_priority_access if {
    input.user.role == "government"
    input.user.government_level in ["federal", "provincial"]
    input.user.verified_government
}

# Enhanced rate limits for government users
user_rate_limit := 50000 if {
    government_priority_access
} else := user_rate_limit

# Data quality policy validation access
allow_policy_validation if {
    input.user.authenticated
    input.user.role in ["admin", "researcher"]
}

allow_policy_validation if {
    government_priority_access
}

# Real-time monitoring access
allow_monitoring_access if {
    input.user.role == "admin"
}

allow_monitoring_access if {
    input.user.role == "government"
    input.user.monitoring_permissions
}