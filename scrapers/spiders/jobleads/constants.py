# JobLeads Categories and Subcategories

job_categories = {
    "Bio & Pharmacology & Health": [
        {"id": "51", "name": "Biology, Biotech & Chemistry"},
        {"id": "52", "name": "Healthcare"},
        {"id": "125", "name": "Medical, Bio & Pharmaceutical Sales"},
        {"id": "53", "name": "Physicians & Doctors"},
        {"id": "55", "name": "Research, development and laboratory"}
    ],
    "Consulting": [
        {"id": "117", "name": "Engineering Consulting"},
        {"id": "111", "name": "Finance Consulting"},
        {"id": "112", "name": "Human Capital"},
        {"id": "116", "name": "IT, Technology & SAP"},
        {"id": "152", "name": "Legal Consulting"},
        {"id": "149", "name": "Life Science & Pharmacology & Health"},
        {"id": "114", "name": "Management & Strategy"},
        {"id": "113", "name": "Marketing & Sales"},
        {"id": "150", "name": "Public Sector"}
    ],
    "Engineering": [
        {"id": "81", "name": "Architecture, Planning & Construction"},
        {"id": "86", "name": "Automotive Engineering"},
        {"id": "87", "name": "Aviation & Aerospace"},
        {"id": "138", "name": "Business Engineering & Management"},
        {"id": "82", "name": "Design & Development"},
        {"id": "84", "name": "Electrical & Energy Engineering"},
        {"id": "154", "name": "Electricians & Technicians"},
        {"id": "139", "name": "Installation, Maintenance & Repair"},
        {"id": "137", "name": "Manufacturing & Production"},
        {"id": "95", "name": "Measurement & Control Technology"},
        {"id": "88", "name": "Mechanical Engineering and Toolmaking"},
        {"id": "155", "name": "Mechanics, Machinists & Tool Operators"},
        {"id": "93", "name": "Physics"},
        {"id": "91", "name": "Plastics & Process Engineering"},
        {"id": "140", "name": "Quality Engineering"},
        {"id": "92", "name": "Technical Sales Engineering"},
        {"id": "89", "name": "Telecommunication & Information Technology"}
    ],
    "Finance": [
        {"id": "14", "name": "Audit, Taxes & Accounting"},
        {"id": "15", "name": "Banking & Lending"},
        {"id": "13", "name": "Controlling"},
        {"id": "16", "name": "Corporate Finance & Strategic Planning"},
        {"id": "20", "name": "Finance & Insurance"},
        {"id": "17", "name": "Financial Advice & Private Banking"},
        {"id": "18", "name": "Investing & Investment Banking"},
        {"id": "21", "name": "Real Estate"},
        {"id": "19", "name": "Risk Management & Quantitative Analysis"}
    ],
    "Human Resources": [
        {"id": "22", "name": "Compensation & Benefits"},
        {"id": "24", "name": "General HR"},
        {"id": "27", "name": "HR & Organizational Development"},
        {"id": "28", "name": "HR Marketing & Recruiting"},
        {"id": "123", "name": "HR Services"},
        {"id": "26", "name": "HR Strategy & Management"}
    ],
    "IT & Technology": [
        {"id": "71", "name": "Database, Analytics & BI"},
        {"id": "72", "name": "IT Management & IT Project Management"},
        {"id": "80", "name": "IT Sales"},
        {"id": "73", "name": "Networks & Systems"},
        {"id": "74", "name": "Professional Services"},
        {"id": "75", "name": "Quality Management"},
        {"id": "136", "name": "SAP"},
        {"id": "78", "name": "Software Architecture & Engineering"},
        {"id": "77", "name": "Software Development"},
        {"id": "79", "name": "Technical Support & Administration"}
    ],
    "Legal": [
        {"id": "38", "name": "Corporate Law"},
        {"id": "120", "name": "Other Legal Services"},
        {"id": "39", "name": "Public Law"}
    ],
    "Management & Operations": [
        {"id": "59", "name": "Business Development & Strategy"},
        {"id": "131", "name": "Business Intelligence & Analysis"},
        {"id": "66", "name": "Change Management & Restructuring"},
        {"id": "130", "name": "Compliance & Regulatory Affairs"},
        {"id": "58", "name": "Customer Service"},
        {"id": "132", "name": "E-Commerce"},
        {"id": "61", "name": "Management & Leadership"},
        {"id": "129", "name": "Operations & Business Administration"},
        {"id": "62", "name": "Plant, Facility & Center Management"},
        {"id": "128", "name": "Product Management"},
        {"id": "63", "name": "Project & Process Management"},
        {"id": "60", "name": "Purchasing & Procurement"},
        {"id": "64", "name": "Quality Management & Operations"},
        {"id": "65", "name": "Supply Chain, Logistics & Transportation"},
        {"id": "127", "name": "Trade, Import & Export"}
    ],
    "Marketing & Media": [
        {"id": "40", "name": "Advertising"},
        {"id": "43", "name": "Communication & PR"},
        {"id": "44", "name": "Creative"},
        {"id": "42", "name": "Event Management"},
        {"id": "49", "name": "Marketing Management"},
        {"id": "50", "name": "Media & Information"},
        {"id": "46", "name": "Online Marketing"},
        {"id": "41", "name": "Product & Brand Marketing"}
    ],
    "Other": [
        {"id": "143", "name": "Agriculture, Forestry, Fishing, and Hunting"},
        {"id": "101", "name": "Art & Culture"},
        {"id": "96", "name": "Assistance"},
        {"id": "142", "name": "Charity"},
        {"id": "146", "name": "Food Production & Safety"},
        {"id": "98", "name": "Health, Safety & Environment"},
        {"id": "100", "name": "Hospitality & Leisure"},
        {"id": "157", "name": "Protective Services"},
        {"id": "145", "name": "Public Sector, Administration & Politics"},
        {"id": "102", "name": "Science, Research and Teaching"},
        {"id": "144", "name": "Sports"},
        {"id": "97", "name": "Training & Coaching"},
        {"id": "148", "name": "Utility & Waste Management"}
    ],
    "Sales": [
        {"id": "119", "name": "General Sales"},
        {"id": "70", "name": "Sales Management"},
        {"id": "69", "name": "Sales Support"}
    ]
}

# Simple list format (category names only)
category_names = [
    "Bio & Pharmacology & Health",
    "Consulting",
    "Engineering",
    "Finance",
    "Human Resources",
    "IT & Technology",
    "Legal",
    "Management & Operations",
    "Marketing & Media",
    "Other",
    "Sales"
]

# Flat list of all subcategories with their IDs
all_subcategories = []
for category, subcats in job_categories.items():
    for subcat in subcats:
        all_subcategories.append({
            "category": category,
            "id": subcat["id"],
            "name": subcat["name"]
        })

countries_dict = {
    "Argentina": "ARG",
    "Australia": "AUS",
    "Austria": "AUT",
    "Bahrain": "BHR",
    "Belgium": "BEL",
    "Brazil": "BRA",
    "Canada": "CAN",
    "Chile": "CHL",
    "Colombia": "COL",
    "Denmark": "DNK",
    "Finland": "FIN",
    "France": "FRA",
    "Germany": "DEU",
    "Hong Kong": "HKG",
    "India": "IND",
    "Indonesia": "IDN",
    "Ireland": "IRL",
    "Italy": "ITA",
    "Kuwait": "KWT",
    "Malaysia": "MYS",
    "Mexico": "MEX",
    "Netherlands": "NLD",
    "New Zealand": "NZL",
    "Norway": "NOR",
    "Oman": "OMN",
    "Pakistan": "PAK",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Portugal": "PRT",
    "Qatar": "QAT",
    "Saudi Arabia": "SAU",
    "Singapore": "SGP",
    "South Africa": "ZAF",
    "Spain": "ESP",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Turkey": "TUR",
    "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
    "United States": "USA",
    "Venezuela": "VEN"
}
