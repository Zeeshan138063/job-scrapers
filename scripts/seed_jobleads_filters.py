import os
from sqlmodel import Session, create_engine, select
from api.models import FilterDefinition, FilterOption, SpiderConfig

def seed_jobleads_filters():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set.")
        return

    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # Ensure 'jobleads' spider exists in scraper_spider_configs
        stmt = select(SpiderConfig).where(SpiderConfig.spider_id == "jobleads")
        jobleads_config = session.exec(stmt).first()
        if not jobleads_config:
            jobleads_config = SpiderConfig(
                spider_id="jobleads",
                search_queries=["python"],
                locations=["USA"]
            )
            session.add(jobleads_config)
            session.commit()
            session.refresh(jobleads_config)

        # 1. Define 'country' filter
        country_def = FilterDefinition(
            spider_id="jobleads",
            filter_key="country",
            display_name="Country",
            filter_type="select",
            is_nested=False,
            default_value="USA"
        )
        session.add(country_def)
        session.flush()

        countries = [
            ("United States", "USA"), ("Germany", "DEU"), ("Netherlands", "NLD"),
            ("United Kingdom", "GBR"), ("France", "FRA"), ("Canada", "CAN"),
            ("Australia", "AUS"), ("Pakistan", "PAK")
        ]
        for label, val in countries:
            session.add(FilterOption(filter_definition_id=country_def.id, option_label=label, option_value=val))

        # 2. Define 'daysReleased' filter
        days_def = FilterDefinition(
            spider_id="jobleads",
            filter_key="daysReleased",
            display_name="Posting Date (Days Ago)",
            filter_type="select",
            is_nested=True,
            default_value="31"
        )
        session.add(days_def)
        session.flush()
        
        for label, val in [("Last 24 hours", "1"), ("Last 7 days", "7"), ("Last 14 days", "14"), ("Last 31 days", "31")]:
            session.add(FilterOption(filter_definition_id=days_def.id, option_label=label, option_value=val))

        # 3. Define 'channels' (Categories) filter - JobLeads uses 'channels' for these IDs
        categories_def = FilterDefinition(
            spider_id="jobleads",
            filter_key="channels",
            display_name="Job Categories",
            filter_type="select",
            is_nested=True,
            default_value="0",
            description="JobLeads uses 'channels' to represent industry sectors/categories."
        )
        session.add(categories_def)
        session.flush()

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

        for category, subcats in job_categories.items():
            for subcat in subcats:
                session.add(FilterOption(
                    filter_definition_id=categories_def.id,
                    option_label=subcat["name"],
                    option_value=subcat["id"],
                    group_name=category
                ))

        session.commit()
        print("Successfully seeded Jobleads filters with hierarchical categories.")

if __name__ == "__main__":
    seed_jobleads_filters()
