package openpolicy.data_quality

import future.keywords.if
import future.keywords.in

# Federal bill validation policy
federal_bill_valid[bill] if {
    bill.identifier
    regex.match(`^[CS]-\d+$`, bill.identifier)
    bill.title
    count(bill.title) > 10
    count(bill.title) < 300
    bill.status in valid_statuses
}

valid_statuses := [
    "First Reading",
    "Second Reading", 
    "Committee Stage",
    "Report Stage",
    "Third Reading",
    "Consideration by Senate",
    "Consideration by House of Commons",
    "Royal Assent",
    "Withdrawn",
    "Defeated",
    "Prorogued",
    "Died on Order Paper"
]

# Enhanced federal bill quality check
federal_bill_quality_score[score] if {
    bill := input.bill
    
    # Base score
    base_score := 50
    
    # Identifier check (+20 points)
    identifier_score := 20 if {
        regex.match(`^[CS]-\d+$`, bill.identifier)
    } else := 0
    
    # Title quality (+25 points)
    title_score := 25 if {
        bill.title
        count(bill.title) >= 20
        count(bill.title) <= 200
        contains(lower(bill.title), "act")
    } else := 10 if {
        bill.title
        count(bill.title) >= 10
    } else := 0
    
    # Status validity (+15 points)
    status_score := 15 if {
        bill.status in valid_statuses
    } else := 0
    
    # Completeness (+15 points)
    completeness_score := 15 if {
        bill.identifier
        bill.title
        bill.status
        bill.summary
    } else := 10 if {
        bill.identifier
        bill.title
        bill.status
    } else := 5 if {
        bill.identifier
        bill.title
    } else := 0
    
    # Freshness (+25 points based on update age)
    freshness_score := 25 if {
        bill.updated_at
        age_hours := time_diff_hours(bill.updated_at)
        age_hours <= 24
    } else := 15 if {
        bill.updated_at
        age_hours := time_diff_hours(bill.updated_at)
        age_hours <= 168  # 1 week
    } else := 5 if {
        bill.updated_at
    } else := 0
    
    score := base_score + identifier_score + title_score + status_score + completeness_score + freshness_score
}

# Helper function to calculate hours difference (simplified)
time_diff_hours(timestamp) := hours if {
    # This would be calculated by the calling application
    # OPA doesn't have direct time arithmetic, so we'll expect this to be pre-calculated
    hours := input.age_hours
}

# Provincial data completeness policy
provincial_data_complete[jurisdiction] if {
    jurisdiction.type == "provincial"
    jurisdiction.representatives
    count(jurisdiction.representatives) > 0
    jurisdiction.name
    jurisdiction.name != ""
    jurisdiction.province
}

# Enhanced provincial data quality
provincial_data_quality_score[score] if {
    jurisdiction := input.jurisdiction
    jurisdiction.type == "provincial"
    
    base_score := 40
    
    # Basic info (+20 points)
    basic_info_score := 20 if {
        jurisdiction.name
        jurisdiction.province
        jurisdiction.type
    } else := 10 if {
        jurisdiction.name
        jurisdiction.province
    } else := 0
    
    # Representatives (+25 points)
    reps_score := 25 if {
        jurisdiction.representatives
        count(jurisdiction.representatives) >= 20  # Minimum expected for provinces
    } else := 15 if {
        jurisdiction.representatives
        count(jurisdiction.representatives) >= 5
    } else := 5 if {
        jurisdiction.representatives
        count(jurisdiction.representatives) > 0
    } else := 0
    
    # Bills (+20 points)
    bills_score := 20 if {
        jurisdiction.bills
        count(jurisdiction.bills) >= 10
    } else := 10 if {
        jurisdiction.bills
        count(jurisdiction.bills) > 0
    } else := 0
    
    # Population data (+15 points)
    population_score := 15 if {
        jurisdiction.population
        jurisdiction.population > 100000  # Reasonable minimum for provinces
    } else := 5 if {
        jurisdiction.population
        jurisdiction.population > 0
    } else := 0
    
    score := base_score + basic_info_score + reps_score + bills_score + population_score
}

# Municipal data quality policy  
municipal_data_quality[jurisdiction] if {
    jurisdiction.type == "municipal"
    jurisdiction.name
    jurisdiction.province
    jurisdiction.population
    jurisdiction.population > 0
}

# Enhanced municipal data quality scoring
municipal_data_quality_score[score] if {
    jurisdiction := input.jurisdiction
    jurisdiction.type == "municipal"
    
    base_score := 50
    
    # Basic municipal info (+25 points)
    basic_score := 25 if {
        jurisdiction.name
        jurisdiction.province
        jurisdiction.type
    } else := 15 if {
        jurisdiction.name
        jurisdiction.province
    } else := 0
    
    # Population (+20 points)
    population_score := 20 if {
        jurisdiction.population
        jurisdiction.population >= 1000
    } else := 10 if {
        jurisdiction.population
        jurisdiction.population > 0
    } else := 0
    
    # Representatives (+15 points)
    reps_score := 15 if {
        jurisdiction.representatives
        count(jurisdiction.representatives) >= 3  # Mayor + councillors
    } else := 8 if {
        jurisdiction.representatives
        count(jurisdiction.representatives) >= 1  # At least mayor
    } else := 0
    
    # Municipal bills/bylaws (+10 points)
    bills_score := 10 if {
        jurisdiction.bills
        count(jurisdiction.bills) > 0
    } else := 0
    
    score := base_score + basic_score + population_score + reps_score + bills_score
}

# Data freshness policy
data_is_fresh[item] if {
    item.updated_at
    # Expect age_hours to be calculated by calling application
    input.age_hours <= 24  # Data must be less than 24 hours old
}

# Critical bill detection
is_critical_bill[bill] if {
    bill.title
    lower_title := lower(bill.title)
    some keyword in critical_keywords
    contains(lower_title, keyword)
}

is_critical_bill[bill] if {
    bill.summary
    lower_summary := lower(bill.summary)
    some keyword in critical_keywords
    contains(lower_summary, keyword)
}

critical_keywords := [
    "budget", "tax", "taxation", "fiscal", "revenue",
    "healthcare", "health care", "medicare",
    "education", "student", "university", "college",
    "defence", "defense", "military", "armed forces",
    "immigration", "refugee", "citizenship", 
    "employment", "labour", "labor", "worker",
    "economy", "economic", "trade", "commerce",
    "environment", "climate", "carbon", "emissions",
    "justice", "criminal", "court", "legal",
    "privacy", "data protection", "surveillance",
    "infrastructure", "transportation", "transit"
]

# Government bill identification (vs private member bills)
is_government_bill[bill] if {
    bill.identifier
    # Commons government bills: C-1 to C-200
    regex.match(`^C-(\d+)$`, bill.identifier)
    number := to_number(regex.find_n(`\d+`, bill.identifier, 1)[0])
    number <= 200
}

is_government_bill[bill] if {
    bill.identifier
    # Senate government bills: S-1 to S-200  
    regex.match(`^S-(\d+)$`, bill.identifier)
    number := to_number(regex.find_n(`\d+`, bill.identifier, 1)[0])
    number <= 200
}

# Comprehensive data validation result
validation_result := {
    "federal_bills_valid": count([bill | 
        bill := input.bills[_]
        bill.jurisdiction_type == "federal"
        federal_bill_valid[bill]
    ]),
    "provincial_jurisdictions_complete": count([jurisdiction | 
        jurisdiction := input.jurisdictions[_]
        provincial_data_complete[jurisdiction]
    ]),
    "municipal_jurisdictions_quality": count([jurisdiction | 
        jurisdiction := input.jurisdictions[_]
        municipal_data_quality[jurisdiction]
    ]),
    "critical_bills": count([bill | 
        bill := input.bills[_]
        is_critical_bill[bill]
    ]),
    "government_bills": count([bill | 
        bill := input.bills[_]
        is_government_bill[bill]
    ]),
    "fresh_data_items": count([item | 
        item := input.data_items[_]
        data_is_fresh[item]
    ])
}

# Overall quality assessment
overall_quality := "excellent" if {
    total_bills := count(input.bills)
    total_jurisdictions := count(input.jurisdictions)
    
    total_bills > 0
    total_jurisdictions > 0
    
    federal_valid_rate := validation_result.federal_bills_valid / count([bill | 
        bill := input.bills[_]
        bill.jurisdiction_type == "federal"
    ])
    
    federal_valid_rate >= 0.9
    
    provincial_complete_rate := validation_result.provincial_jurisdictions_complete / count([jurisdiction | 
        jurisdiction := input.jurisdictions[_]
        jurisdiction.type == "provincial"
    ])
    
    provincial_complete_rate >= 0.8
}

overall_quality := "good" if {
    not overall_quality == "excellent"
    
    total_bills := count(input.bills)
    total_jurisdictions := count(input.jurisdictions)
    
    total_bills > 0
    total_jurisdictions > 0
    
    federal_bills := [bill | 
        bill := input.bills[_]
        bill.jurisdiction_type == "federal"
    ]
    
    count(federal_bills) > 0
    
    federal_valid_rate := validation_result.federal_bills_valid / count(federal_bills)
    federal_valid_rate >= 0.7
}

overall_quality := "needs_improvement" if {
    not overall_quality == "excellent"
    not overall_quality == "good"
}