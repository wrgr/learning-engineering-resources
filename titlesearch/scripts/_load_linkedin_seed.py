"""One-time script: load all 173 PhantomBuster LinkedIn seed records into people.json.

Tuple schema: (display_name, headline, location, company, job_title, industry, lists, triage_override)
  lists: "tl" = title-all + le-global-keyword, "l" = le-global-keyword only
  triage_override: None = auto, "NEEDS_REVIEW" = flagged false positive
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build_people import load_people, normalize_linkedin_pb_record, save_people, upsert_record

TL = ["title-all", "le-global-keyword"]
L = ["le-global-keyword"]
NR = "NEEDS_REVIEW"

# fmt: off
# (name, headline, location, company, job_title, industry, lists, triage_override)
_RECORDS = [
    # ── Page 1 ────────────────────────────────────────────────────────────────
    ("Destiny Blue", "Learning Engineer · Learning & Development Professional", "Charlotte, North Carolina, United States", "Apple", "Instructional Designer", "Consumer Electronics", TL, None),
    ("Peyton Blaise Wilson", "Boston College Graduate Student | Fulbright Scholar, Learning Engineer, Museum Educator", "Boston, Massachusetts, United States", "Boston College", "Graduate Assistant, McGillycuddy-Logue Fellows Program, Office of Global Education", "Higher Education", TL, None),
    ("Rashid Johnson", "Instructional Leadership Coach | Teaching & Learning Engineer | Data Geek | Private Figure", "New York City Metropolitan Area", "The Renaissance Charter School 2", "Principal", "Higher Education", TL, None),
    ("Samar Elghalban", "Learning Engineer | Co-Founder of Edulga | My views are my startup's views too!", "6th of October, Al Jizah, Egypt", "Edulga", "Founder & CEO", "Higher Education", TL, None),
    ("Thomas Caswell", "Learning Engineer & Edupreneur", "Oswego, New York, United States", "ClassroomRevolution, LLC", "Co-Founder & Managing Partner", "E-learning", TL, None),
    ("Charles Broussin", "Founder & CEO @Proxxie | Learning Engineer | Educator", "Biarritz, Nouvelle-Aquitaine, France", "Proxxie", "Founder & CEO", "Higher Education", TL, None),
    ("Farah Mubarkeh, MSc", "STEM Learning Engineer | STEM Instructional Designer | Adaptive Learning (Area9 Rhapsode) | Curriculum & Assessment Specialist | EdTech", "Jordan", "CTS - Creative Technology Solutions", "Learning Engineer (STEM)", "Computer Software", TL, None),
    ('David "Blackmagic" Elahee', "Code artist & Boss at Headbang Club - Learning Engineer and Coordinator of Software Engineering sector at ENJMIN", "Gond-Pontouvre, Nouvelle-Aquitaine, France", "CNAM-Enjmin", "Coordinator and Learning engineer of the Software Engineering sector at ENJMIN", "", TL, None),
    ("Mike Partridge", "Learning Engineer | Business Technology Faculty", "Rochester, New York, United States", "Golisano Institute for Business & Entrepreneurship", "Business Technology Faculty", "Higher Education", L, None),
    ("Michelle S. Fernández", "Learning Engineer at Carnegie Mellon University", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Learning Engineer - School of Computer Science", "Higher Education", L, None),
    ("Ingrid C.", "Learning Architect · Learning Engineer · Instructional Designer · Instructional Developer", "Greater Philadelphia", "Healthcare", "Learning Architect", "", L, None),
    ("Aleksandra Ambroziak", "Instructional Designer & Learning Engineer, Tabletop Gaming Enthusiast", "Philadelphia, Pennsylvania, United States", "Carnegie Mellon University", "Learning Engineer", "Higher Education", L, None),
    ("Nicole M.", "Learning Engineer ‣ Graduate Alumna at The Johns Hopkins University", "Potomac, Maryland, United States", "DTS", "Instructional Systems Designer", "Information Technology & Services", L, None),
    ("Kelly Cooney", "Learning Engineer & Head of Operations | Life Design Advocate | Adjunct Faculty | Creator of Impactful, Research-Driven Learning Experiences", "Sykesville, Maryland, United States", "The Johns Hopkins University", "Learning Engineer - Center for Staff Life Design", "Higher Education", L, None),
    ("Harley Chang", "Learning Engineer at Carnegie Mellon University | M.S. Learning Engineering, MBA Tech Strategy and Product Management", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Learning Engineer", "Higher Education", L, None),
    ("Uzma Khan", "Fulbright Scholar | EdTech | Product | Learning Engineer | Creating Impact in Education", "Bethlehem, Pennsylvania, United States", "Taleemabad", "Product Manager", "E-learning", L, None),
    ("Mollie McCormick, Prosci", "Supporting change, innovation, and getting things done for the workforce as Learning Experience Designer | Change Manager | Learning Engineer | Strategic Project Manager", "Mount Airy, Maryland, United States", "National Park Service", "Lead Instructional Designer / Project Manager", "Government Administration", L, None),
    ("Utsab Saha", "Learning Engineer at California State University, Monterey Bay", "Fremont, California, United States", "California State University, Monterey Bay", "Lecturer In Computer Science", "Higher Education", L, None),
    ("Jules Pasley", "Learning Engineer", "Jeffersonville, Indiana, United States", "Abilene Christian University", "Learning Engineer", "Higher Education", L, None),
    ("Eric Regnell", "Education Professional and Learning Engineer", "Manchester, New Hampshire, United States", "Institute of Management Accountants (IMA)", "Curriculum Designer - Contract", "Higher Education", L, None),
    ("Jason Bock", "Director for Online Education | Learning Engineer | AI Higher Education Expert | Instructional Designer | AI EdTech Founder | Performance Improvement Technologist", "Morgantown, West Virginia, United States", "West Virginia University", "Director of Online Education", "Higher Education", L, None),
    ("Joey Huang", "Assistant Professor at NC State University | Learning Scientist | Learning Designer | Learning Engineer", "Raleigh, North Carolina, United States", "North Carolina State University", "Assistant Professor", "Higher Education", L, None),
    ("Jess Barney", "Learning Engineer and Adjunct Faculty", "Peterborough, New Hampshire, United States", "Southern New Hampshire University", "Learning Engineer", "Higher Education", L, None),
    ("Daniel Montaño", "Quick-learning engineer with a passion for service", "Spokane-Coeur d'Alene Area", "Enercon Services, Inc.", "Principal I&C Engineer", "Utilities", L, NR),
    ("Scarlett Shi", "Senior UX Researcher @Dynatrace | Learning Engineer | Educator", "Greater Boston", "Dynatrace", "Senior UX Researcher I", "Computer Software", L, None),
    ("Elizabeth Burnham, PMP, CTS-D", "Training Leader | Project Manager | Curriculum Strategist | Learning Engineer | Technology Driven | Veteran", "Baltimore, Maryland, United States", "Pershing Technologies", "Training & QA/QC Coordinator", "Information Technology & Services", L, None),
    ("Virginie Olive", "Senior Medical Learning Engineer at Area9 Lyceum", "Tucson, Arizona, United States", "Area9 Lyceum", "Senior Medical Learning Engineer", "Higher Education", L, None),
    ("Marsha K.", "Learning Engineer | Instructional Designer | Transformational Game Designer | Multimedia Professional", "Reston, Virginia, United States", "Noblis", "Jr. Instructional Systems Designer", "Information Technology & Services", L, None),
    ("Jatelvis Sharpe", "AF Career Development Academy, Learning Engineer", "Crestview-Fort Walton Beach-Destin Area", "United States Air Force", "Learning Engineer", "Defense & Space", L, None),
    ("Marc Siskin", "Former Learning Engineer and Manager of Carnegie Mellon University Modern Language Resource Center", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Manager", "Higher Education", L, None),
    ("Dr. Steve Rappleyea", "Keynote Speaker, Senior Consultant, Learning Engineer, and MTSS Ambassador", "Modena, New York, United States", "University at Albany", "New York State MTSS-I Coach", "Higher Education", L, None),
    ("Dieyu (Della) Ouyang", "Learning Engineer | CMU HCII METALS '24", "Pittsburgh, Pennsylvania, United States", "National Tsing Hua University", "Research Assistant", "Research", L, None),
    ("Tim Hayes", "Lead Digital Learning Engineer / Senior Front-End Developer", "Alexandria, Virginia, United States", "Systems Plus, Inc.", "Lead Digital Learning Engineer", "Management Consulting", L, None),
    ("Gregory Bousley", "Learning Engineer - Game Developer - Instructional Designer", "United States", "Hyland", "Instructional Designer 4", "Computer Software", L, None),
    ("Hector Cervantes", "Ever learning engineer", "Dayton, Ohio, United States", "Modern Technology Solutions, Inc. (MTSI)", "Principal Software Development Engineer", "Defense & Space", L, NR),
    ("Kaleb M.", "Learning Engineer | PhD in Experimental Psychology", "Pittsburgh, Pennsylvania, United States", "Carnegie Learning", "Learning Engineer", "Higher Education", L, None),
    ("Jennifer Leone T.", "AI Learning Developer | Senior Instructional Designer & Learning Engineer | 508 Compliance | Gamification | Storyline 360", "Washington DC-Baltimore Area", "Medium", "Freelance Writer", "Internet", L, None),
    ("Anastasia Tompkins", "Learning Engineer", "Biloxi, Mississippi, United States", "United States Air Force", "Learning Engineer", "Defense & Space", L, None),
    ("Thomas Evans", "Systems Design & Testing | Learning Engineer | Builder of Scalable, Human-Centered Experiences", "Columbus, Ohio, United States", "Transportation Research Center Inc.", "Autonomous Specialist", "Information Technology & Services", L, None),
    ("Michael Goudzwaard", "Senior Associate Director of Learning Innovation | Learning Engineer, Generative AI, Innovation Leader, Inclusion Advocate", "Greater Boston", "Dartmouth College", "Senior Associate Director of Learning Innovation", "Higher Education", L, None),
    ("Kevin Amrich, MIM", "AETC Learning Engineer at US Air Force", "Biloxi, Mississippi, United States", "United States Air Force", "precision measurement equipment labortory technician", "Defense & Space", L, None),
    ("Luciano Iorizzo", "Learning Engineer", "Williamsburg, Virginia, United States", "", "Retired", "", L, None),
    ("Avi Chawla", "Senior Learning Engineer at Carnegie Mellon University | MBA Candidate, CMU Tepper School of Business", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Senior Learning Engineer", "Higher Education", L, None),
    ("Lauren Totino", "Learning Engineer at Massachusetts Institute of Technology", "Greater Boston", "Massachusetts Institute of Technology", "Learning Engineer", "Higher Education", L, None),
    ("YUE WANG", "Curriculum Product Manager | Learning Engineer at CMU", "Santa Clara, California, United States", "Open Learning Initiative", "Learning Engineer", "E-learning", L, None),
    ("Shijie Zhu", "Learning Engineer Intern at TEEL lab and graduate student from Carnegie Mellon University", "Pittsburgh, Pennsylvania, United States", "TEEL lab", "Research Assistant Intern", "", L, None),
    ("Jessica Blackwell", "Senior Learning Engineer | Collaborative Communicator | Trusted Problem Solver", "United States", "Wisewire", "Senior Learning Engineer", "Education Management", L, None),
    ("Karen N.", "Learning Engineer in Educational Technology", "Pittsburgh, Pennsylvania, United States", "Capstone project with an EdTech industry client", "Project Lead", "", L, None),
    ("John Holmlund", "Learning Engineer, Knowledge Architect--Looking for teaching positions with support for divergent and lateral thinking.", "St Paul, Minnesota, United States", "Our Homes, rental property management", "Owner/Manager", "", L, None),
    ("Adam DuQuette", "Developer Learning Engineer at Tech Soft 3D", "Redmond, Oregon, United States", "Tech Soft 3D", "Developer Learning Engineer", "Computer Software", L, None),
    # ── Page 2 ────────────────────────────────────────────────────────────────
    ("Leston Drake PhD", "Experienced Learning Engineer and Business Leader", "Salt Lake City Metropolitan Area", "LetterPress Consulting", "President", "E-learning", L, None),
    ("Manvi Teki", "Learning Engineer @ Carnegie Mellon USA - Africa | International Education | Data and Impact | Learning Science", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Learning Engineer", "Higher Education", L, None),
    ("Lynn Kojtek", "Learning Engineer at Carnegie Mellon University, CPACC certified", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Learning Engineer", "Higher Education", L, None),
    ("Anna L.", "Lead Learning Engineer at Northwestern University", "Evanston, Illinois, United States", "Northwestern University", "Lead Learning Engineer", "Higher Education", L, None),
    ("Patricia Calle", "Instructional Designer & Learning Engineer | Digital Learning & Web Experience Designer | Bilingual Spanish/English | Founder, Innovate Montessori Academy", "Raleigh-Durham-Chapel Hill Area", "Evergreen Rose Farm", "Marketing Manager & Web Developer", "", L, None),
    ("Jay Leone", "AI Integration Specialist | Senior Learning Engineer | AI Trainer & Prompt Engineering Expert | Bridging Human-Centered Design, Learning Science, and Generative AI Innovation", "Durham, New Hampshire, United States", "Southern New Hampshire University", "Senior Learning Engineer", "Higher Education", L, None),
    ("Nikkole Braun", "Learning Engineer at Health Catalyst", "Salt Lake City, Utah, United States", "Health Catalyst", "Learning Engineer", "Information Technology & Services", L, None),
    ("Henry Chang", "Learning Engineer | Software Engineer", "Greater Pittsburgh Region", "NoRILLA", "Lead Software Engineer", "E-learning", L, None),
    ("Korinn Ostrow, Ph.D.", "Senior Learning Engineer @ Edmentum", "Greater Boston", "Edmentum", "Senior Learning Engineer", "E-learning", L, None),
    ("Julie Lawrence, Ed.D.", "Instructional Design Leader, Learning Engineer, Project Manager | Doctor of Education - EdD", "Greater Chicago Area", "Collegis Education", "Supervisor - Instructional Design", "Education Management", L, None),
    ("Emily Jennings", "Learning Engineer", "Opelika, Alabama, United States", "Lee County Board of Education", "Classroom Teacher", "", L, None),
    ("Viviana Kypraios", "Project Manager / Learning Engineer / Sim Analyst", "Orlando, Florida, United States", "", "Freelance Analyst", "", L, None),
    ("Brandt Dargue", "Sr. Learning Engineer at Boeing", "Hazelwood, Missouri, United States", "Boeing", "Sr. Learning Engineer", "Aviation & Aerospace", L, None),
    ("Alysson Hursey Bullington", "Learning Experience Designer, Learning Program Architect, Full-stack Learning Engineer", "Huntsville, Alabama, United States", "ScienceLogic", "Senior Instructional Designer/Learning Engineer", "Computer Software", L, None),
    ("Chloe Ullah", "Learning Technology Learning Engineer", "Santa Monica, California, United States", "United States Air Force", "Learning Engineer", "Defense & Space", L, None),
    ("Jeremy Durelle", "AI in Education Advocate | Creator of ScoreWise AI | Founder @ FusionLabs | Dual M.S. | Data & Learning Engineer", "Dubuque, Iowa, United States", "Fusion Labs LLC", "Founder & CEO", "", L, None),
    ("Ting Chen", "Keep Learning Engineer; Apache Pinot PMC, Committer", "San Francisco Bay Area", "Uber", "Senior Staff Engineer", "Internet", L, NR),
    ("Ryan Scarbrough", "Principal Learning Engineer | L&D Architect | AI Strategy & Literacy", "Louisville Metropolitan Area", "Humana", "Senior Software Engineer, IT Learning Strategies", "Insurance", L, None),
    ("Reginald C. Jackson, Ed.D.", "Director Teaching Excellence, Medill School of Journalism and Lead Learning Engineer, NUIT at Northwestern University", "Chicago, Illinois, United States", "Northwestern University", "Director Teaching Excellence, Medill School of Journalism and Lead Learning Engineer, NUIT", "Higher Education", L, None),
    ("Nathan Pierce", "Future-Forward Educator | Learning Engineer", "Redwood City, California, United States", "Design Tech High School at Oracle", "Educator", "Education Management", L, None),
    ("Sydney Evans", "Learning Engineer @ Tripalink | Instructional Design, Customer Success, Implementation/Enablement", "Los Angeles Metropolitan Area", "Tripalink", "Customer Success Manager", "Computer Software", L, None),
    ("David Stauffer", "Provocative Thinker, Entrepreneur, Learning Engineer – Dedicated to igniting innovative ideas and fostering an insatiable curiosity", "United States", "NexStori", "Founder", "", L, None),
    ("Alexis Griffith-Waye (she and her)", "Learning Engineer | Strategists | Analyst | Senior Advisor", "Greater Boston", "Eastern Bank", "Talent Development Partner", "Banking", L, None),
    ("Heather Saigo", "BS, MS, EdD; Educator, Researcher, Learning Engineer, Catalyst for Organizational Change. Can you solve problems using the same strategies that created them? No! Education is ripe for transformation. Let's go!", "United States", "Oregon Institute of Technology", "Instructional Designer", "Higher Education", L, None),
    ("Beth Gilliland", "Learning Engineer at the Tessitura Network", "Providence County, Rhode Island, United States", "Tessitura", "Director of Learning Systems", "Computer Software", L, None),
    ("Younes Rabia", "Digital Learning Engineer | IT", "Prefecture of Casablanca, Casablanca-Settat, Morocco", "Office national de l'electricité et de l'eau potable - Branche Electricité", "Ingénieur pédagogique multimédia", "Government Administration", L, None),
    ("Aaron Goldstein", "Learning Engineer | Manager of Data & Learning Resources at KIPP Public Schools", "United States", "KIPP Tulsa Public Charter Schools", "Data & Learning Resource Manager", "Education Management", L, None),
    ("Bea Jimenez", "Learning Engineer & Designer | AI-Driven Learning | Coach | 2025 IT Employee of the Year | MSLOC @ Northwestern University", "Chicago, Illinois, United States", "Northwestern University", "Learning Engineer", "Higher Education", L, None),
    ("Karina Luna", "Doctoral Student & Faculty Associate ▶ Human-Centric Media Scholar ▶ Learning Engineer ▶ Critical Media Literacy Education", "Scottsdale, Arizona, United States", "Walter Cronkite School of Journalism and Mass Communication at Arizona State University", "Faculty and Research Associate", "Higher Education", L, None),
    ("Jennalee Win Bollinger", "Future Learning Engineer | Instructional Design + LXD + eLearning Development | Purdue MSEd Learning Design and Technology | UX/UI eLearning", "United States", "Kairos Pacific University of California", "Admissions Counselor", "Higher Education", L, None),
    ("Lauren Jamerson", "Senior Learning Academy Specialist | Adaptive Learning Engineer | Instructional Designer | Global L&D Professional", "United States", "Aptia Group", "Senior Learning Academy Specialist", "Information Technology & Services", L, None),
    ("Sandra Fong", "Educator and digital learning engineer", "Australia", "BiCortex Languages", "English Teacher", "Education Management", L, None),
    ("Michael Paul", "Active TS/SCI, Project Manager, Avionics Technician, Technical Writer & Editor, Learning Engineer, Career Development Manager, GMDSS, GROL", "United States", "United States Air Force", "Learning Engineer/ Career Development Course Program Manager", "Defense & Space", L, None),
    ("Kavya Chenna", "Learning Engineer at Novartis Healthcare Pvt Ltd, Human Resources", "Greater Hyderabad Area", "Novartis", "Learning Engineer", "Pharmaceuticals", L, None),
    ("Nora Puskas", "Learning Engineer at Area9 Lyceum", "Sant Cugat del Vallès, Catalonia, Spain", "Area9 Lyceum", "Instructional Designer | Learning Engineer", "", L, None),
    ("Ismael Nava", "Learning Engineer/ Technowizard. Learning and Development: ID/E-Learning Developer, and Cyber Security Training Consultant.", "San Antonio, Texas, United States", "", "ISD/ E-Learning Dev/ Project Manager", "", L, None),
    ("Caroline CUEFF", "Digital Learning Engineer à La Redoute", "Moissy-Cramayel, Île-de-France, France", "La Redoute", "Digital Learning Engineer", "Retail", L, None),
    ("Rasha Alzebdieh", "STEM Learning Engineer Adaptive Learning Specialist E-learning Specialist", "Jordan", "CTS", "Senior Learning Engineer", "E-learning", L, None),
    ("Fadwa A.", "Senior Instructional Designer | Learning Engineer", "Amman, Jordan", "Jordan River Foundation", "Training Instructional Designer", "Non-profit Organization Management", L, None),
    ("Fernando Gómez Tercero", "E-learning Engineer & DTP Specialist", "Valencian Community, Spain", "", "E-learning / DTP specialist, translator", "", L, None),
    ("Ahammed Shehin", "Aspiring Mechine Learning Engineer", "Kozhikode, Kerala, India", "", "", "", L, NR),
    ("PUGALARASAN R", "Creative & Fast-Learning Engineer | Proficient in SPP&ID & AVEVA E3D | Piping Equipment Structure Electrical", "Chennai, Tamil Nadu, India", "Kagira Drawing Solution", "Piping & Instrumentation Designer (Trainee)", "E-learning", L, NR),
    ("Aastha Patel", "Learning Engineer | Creating a world where children love to learn", "Rajkot, Gujarat, India", "", "Independent Consultant", "", L, None),
    ("Gokul D", "developer- meaching learning engineer", "Erode, Tamil Nadu, India", "", "", "", L, NR),
    ("Ildiko Kovacs", "Senior Learning Engineer and Implementation Manager @ Area9 Lyceum", "Germany", "Area9 Lyceum", "Senior Learning engineer & Implementation Manager", "Higher Education", L, None),
    ("Dr. Patrick D.", "Fachmanager Explosionsschutz · Adaptive Learning Engineer", "Germany", "Dyrba Explosionsschutz Bildung u. Beratung", "Fachmanager Explosionsschutz", "", L, None),
    ("Muhammad Rizky Zanuar", "IT Learning Engineer & Founder Zhan Group | Hospitality Professional Turned Tech Entrepreneur | Ed-Tech & FinTech Solutions", "Malang, East Java, Indonesia", "Zhan Group", "Founder & IT Learning Engineer", "", L, None),
    ("Beverley Ramos", "Learning Engineer | Training Solutions Expert | AI Enabler in Learning and Development", "Metro Manila, National Capital Region, Philippines", "IDC", "Global Learning Systems Manager", "Market Research", L, None),
    ("Vaibhav Deshmukh", "E-learning Engineer at Transperfect Solutions India Private Limited", "Pune Division, Maharashtra, India", "TransPerfect", "E-learning Engineer", "Translation & Localization", L, None),
    ("Angie Bors, MA, ACC", "Learning & OD Consultant • LMS Consultant • Six Sigma Black Belt • ICF Associate Certified Coach • Neurodivergent Thinker • Visual Designer • Learning Engineer", "Minneapolis, Minnesota, United States", "Federal Reserve Bank of Minneapolis", "Learning and OD Consultant Business Analyst Learning Management Support Office", "Banking", L, None),
    # ── Page 3 ────────────────────────────────────────────────────────────────
    ("Georgii BAKHTIIAROV", "Augmented Learning Engineer I Coach", "Paris, Île-de-France, France", "FORSEAD", "Ingénieur pédagogique", "E-learning", L, None),
    ("Rodrigo Palacios", "E-Learning Engineer/DTP Specialist/DTP Lead", "Greater Rosario", "Technelion LLC", "DTP lead", "Information Technology & Services", L, None),
    ("Ayoub Safi", "Senior E-Learning Engineer @ CTS | Academic Writing, TBL", "Amman, Amman, Jordan", "CTS", "Senior E-Learning Engineer", "E-learning", L, None),
    ("Lawrence Nip", "Developer focused on modern software challenges, problem-solving, collaboration and team growth. Fast-learning engineer transitioning into modern software domains.", "London, England, United Kingdom", "Cubic Transportation Systems", "Software Engineer", "Computer Software", L, NR),
    ("Nehala Mumtaz Saboor", "Instructional Designer | Learning Experience Designer | Learning Architect | eLearning Designer | Learning Engineer", "Islāmābād, Pakistan", "Motive", "Instructional Designer", "Computer Software", L, None),
    ("Aditya Agwane", "Robotics Learning Engineer | Building Robots Learning system | AI Operator", "Latur, Maharashtra, India", "", "", "", L, NR),
    ("Fadime AKSOY", "Educational Technology & Learning Engineer | Specialist in Digital Learning Design", "Strasbourg, Grand Est, France", "Inventioneering", "Responsable projet de formation numérique", "Professional Training & Coaching", L, None),
    ("Stacy Antoinette Lattimore", "Computational Linguist |E-Learning Engineer| Localization Specialist| Language Instructor", "Frankfurt Rhine-Main Metropolitan Area", "Lingoda GmbH", "E-Learning Designer/Developer", "E-learning", L, None),
    ("Valeria Gaudenzi", "Senior E-Learning Engineer at TransPerfect", "Berlin, Berlin, Germany", "TransPerfect", "E-Learning Localization Engineer", "Translation & Localization", L, None),
    ("Ani Hovhannisyan", "Learning Engineer | Instructional Designer | Adaptive Learning (Rhapsode™) | Technical Content Engineering | PhD Researcher", "Yerevan, Armenia", "RelyOn (Digital)", "Learning Engineer", "E-learning", L, None),
    ("Amira Mahmoud", "Personalized Learning Engineer, Instructional Design Team Leader, Certified IDLX, Adaptive Learning & E-Learning Design Mapping Expert", "Egypt", "Thaka Holding", "Instructional Design Team Leader", "Information Technology & Services", L, None),
    ("Spyridon Zoumperis", "Learning Engineer", "Athens Metropolitan Area", "Metlen Energy & Metals", "Senior Learning Academies Designer", "Mining & Metals", L, None),
    ("Rekha Mohanty", "Certified Adaptive Learning Engineer passionate about AI-Powered Learning Development", "Toronto, Ontario, Canada", "Bmo Bank of Montreal", "Senior Learning and Experience Designer", "", L, None),
    ("Aya H.", "PhD Student | Instructional Designer & Digital Learning Engineer", "Rabat, Rabat-Salé-Kénitra, Morocco", "Mentor Maroc", "Conceptrice pédagogique multimédia", "Financial Services", L, None),
    ("Melanie Laruan", "Medical Technologist | Public Health Professional | Adaptive Learning Engineer (Area9 Lyceum) | E-learning Course Developer (Articulate 360) | Medical Writer & SEO Experience", "Benguet, Cordillera Admin Region, Philippines", "Zafyre Clinical Education", "Learning Engineer", "E-learning", L, None),
    ("Maria Christou", "Learning designer, learning engineer, science outreach advocate and creator of science-society bridges", "Grenoble, Auvergne-Rhône-Alpes, France", "Grenoble INP - UGA", "Ingénieure pédagogique", "Higher Education", L, None),
    ("William Cronje", "Senior Learning Engineer | Obsessed with how Learning Science and AI intersect to shape the future of learning", "City of Cape Town, Western Cape, South Africa", "Multiverse", "Senior Learning Engineer", "Computer Software", L, None),
    ("Wilson Pulido Acuña", "Educational Course Director | Learning Engineer | Learning and Development Manager | Knowledge Manager | Talent Development Manager", "Bogotá D.C. Metropolitan Area", "Platzi", "Course Director", "E-learning", L, None),
    ("Chloe Simon", "E-learning engineer", "Grenoble, Auvergne-Rhône-Alpes, France", "Université Grenoble Alpes", "PhD student", "Higher Education", L, None),
    ("Michael Ouru, PMP", "Learning Engineer | AI Education Strategist | EdTech | IT, NGO & eLearning Solutions", "Nairobi County, Kenya", "KCA University", "LMS & Media Services Lead", "Higher Education", L, None),
    ("Dzung Vo", "Edtech Product Lead, Learning Engineer/Designer, Rural Education Advocate, Fulbright Scholar", "Ho Chi Minh City, Vietnam", "iMentor", "Founder/Mentor", "Internet", L, None),
    ("Talha Khan", "Learning Engineer | Curriculum Technologist | LMS & EdTech Platforms | SQL, Moodle, H5P | Driving Digital Learning & Assessment Solutions", "WP. Kuala Lumpur, Federal Territory of Kuala Lumpur, Malaysia", "MATLAMAT WAWASAN SDN. BHD", "Learning Platform Specialist", "", L, None),
    ("Ahmed El Kady", "Senior E-Learning Specialist | LMS Administrator (Moodle & Thinqi) | Digital Learning Engineer | Frontend Developer", "Aswan, Egypt", "Aswan University", "Senior E-Learning Specialist | LMS Administrator (Moodle & Thinqi) Aswan University", "Higher Education", L, None),
    ("Boheng Zhang", "Bilingual Learning Engineer in AI-Enhanced Education | Editorial board member of Journal of Family Social Work", "Shenzhen, Guangdong, China", "Guangzhou Gizzai Technology Limited Company", "Learning Engineer-AI Teaching Assistant Division", "Computer Software", L, None),
    ("Lisa Mörs", "Senior Learning Engineer | Bridging Learning Science & Technology to Transform Cybersecurity Awareness Training", "Bornheim, North Rhine-Westphalia, Germany", "SoSafe", "Senior Learning Engineer", "Information Technology & Services", L, None),
    ("Banu Ömür ÇÖLAŞAN", "EdTech Entrepreneur, Learning Engineer, Matematik Öğretmeni, Öğrenme ve Çözüm Kolaylaştırıcısı, Oyun Tasarımcı", "Şişli, Istanbul, Türkiye", "JampGames", "Founder", "", L, None),
    ("Urbain B.", "Senior Software & Machile Learning Engineer @ LAND O'CLOCK", "Kigali City, Rwanda", "LAND O'CLOCK", "Senior Software Engineer", "Computer Software", L, NR),
    ("Ganesh Phalke", "Sr. E-learning Engineer | HTML | CSS | JavaScript | Articulate 360 | Rise | Camtasia | Captivate", "Pune Division, Maharashtra, India", "TransPerfect", "Sr. E-learning Engineer", "Translation & Localization", L, None),
    ("Imène GOUBRID", "Digital Learning Engineer | EdTech, Expert in Digital Learning, Tech Innovation & AI", "Paris, Île-de-France, France", "reseauprosante.fr", "Chargée de développement commercial", "Online Media", L, None),
    ("Karthik Varma Sunchu", "AI Student at SRM AP University | Aspiring Learning Engineer | Python & Data Science Enthusiast | web development | Power Bi", "Hyderabad, Telangana, India", "", "", "", L, NR),
    ("Laura B.", "Learning Engineer | E-Learning Development | Digital Learning & EdTech | (Medical) German Education | Pharma & Healthcare L&D", "Hattersheim, Hesse, Germany", "F+U Schools | Universities | Academies", "E-Learning Developer", "Education Management", L, None),
    ("Nour Alshanty", "Adaptive learning area9 · Senior STEM learning engineer · E-learning systems specialist · Vocational IT trainer · Curriculum designer · e_learning Instructional designer", "Amman, Jordan", "Colleges of Excellence", "IT diploma instructor", "Education Management", L, None),
    ("Nicolas GRONSART", "Cofounder | Learning Engineer | EdTech Innovation | EuraTechnologies", "Greater Lille Metropolitan Area", "Start-up en création", "Cofounder | Learning Engineer | EdTech Innovation", "", L, None),
    ("Riccardo Larini", "Solution Architect and Learning Engineer at Area9 Lyceum · Formatore di docenti, tutor e formatori", "Tallinn Metropolitan Area", "Area9 Lyceum", "Solution Architect", "Higher Education", L, None),
    ("Aude Démarest", "Digital learning engineer", "Lyon, Auvergne-Rhône-Alpes, France", "Avenir Conseil", "Digital learning engineer", "Information Technology & Services", L, None),
    ("Abla Bouhaddou", "Learning Engineer | Teaching Personal & Professional Development | Supporting Student Success Polytech Lyon", "Lyon, Auvergne-Rhône-Alpes, France", "Université Claude Bernard Lyon 1", "Chargée d'enseignement | Polytech Lyon", "Higher Education", L, None),
    ("Franck Buland", "e-Learning engineer", "Francheleins, Auvergne-Rhône-Alpes, France", "Vilocalis", "Entrepreneur", "Internet", L, None),
    ("Dušan Brković", "E-Learning Engineering Department Manager", "Kragujevac, Centralna Srbija, Serbia", "TransPerfect", "E-Learning Engineering Department Manager", "Translation & Localization", L, None),
    ("Nur Syahirah Abdullah", "Committed and values continuous learning engineer to deliver high quality work and has the ability to work on multiple tasks with less supervision yet performing work at the best possible level.", "Federal Territory of Kuala Lumpur, Malaysia", "VC Engineering Sdn Bhd", "Senior Project Engineer", "Construction", L, NR),
    ("Jagdish Singh Sohal (PGCE, MA, FRSA)", "@JustJag Education / Award-Winning Video and Learning Design / Teacher / The Social Learning Engineer / Human Centered Content Design / Multimedia Learning (ML)", "Codsall, England, United Kingdom", "JustJag", "Learning Experience Design, Media and Strategy", "E-learning", L, None),
    ("Ysa Alcantara", "Associate Director, Growth & Strategic Partnerships | SaaS | HR Tech | Adaptive Learning Engineer", "Philippines", "Viventis Search Asia", "Associate Director, Head of Career Technology", "Staffing & Recruiting", L, None),
    ("Aurélia Robert", "Trainer & Learning Experience Designer | Learning Engineer – Soft Skills, English, PBL, AFEST & Gamified Learning", "La Talaudière, Auvergne-Rhône-Alpes, France", "Dev Yourself", "Freelance Trainer | Founder of Dev Yourself", "Professional Training & Coaching", L, None),
    ("Julian Davis", "Learning Systems Architect | Digital Learning Engineer | xAPI | Founder, Remote Reviewer | National Advisory Board Member, ILP APAC", "Greater Brisbane Area", "Remote Reviewer", "Founder", "Computer Software", L, None),
    ("Santiago Ortega Tafur", "Digital Learning Engineer | Online Trainer (Business English, Intercultural Spanish) | Entrepreneurial Student (Pépite) | Notion Campus Leader | Translator (English, French → Spanish)", "Paris, Île-de-France, France", "Université de Rouen", "Lecturer in Spanish", "Higher Education", L, None),
    ("Aaron Pass", "Learning Engineer | Neurotactical | Talent Development", "Wichita Falls, Texas, United States", "Air Force Career Development Academy", "AI Businesss Development Assistant", "", L, None),
    ("Logan B.", "Instructional Systems Designer/Learning Engineer", "Greater Tampa Bay Area", "Citi", "Instructional Designer/Learning Engineer", "Financial Services", L, None),
    ("Jeremy Shaw", "Doctoral Candidate and Learning Engineer", "Salinas, California, United States", "Computing Talent Initiative", "Learning Engineer", "Higher Education", L, None),
    ("Courtney Scalf-Crickenberger", "Developer Learning Engineer | Space & Physics Enthusiast | Programmer", "Palm Bay, Florida, United States", "Tech Soft 3D", "Developer Learning Engineer", "Computer Software", L, None),
    ("Tyree Cowell", "Learning Engineer at Carnegie Learning", "Pittsburgh, Pennsylvania, United States", "Carnegie Learning", "Senior Learning Engineer", "Higher Education", L, None),
    ("Marnie OBrien", "Sr. Instructional Designer | AI Strategy & Training | Learning Engineer | M.Ed., PMP", "Minneapolis, Minnesota, United States", "HOMaxis Group (self)", "Independent Consultant", "", L, None),
    # ── Page 4 ────────────────────────────────────────────────────────────────
    ("Ed Delaney", "Chief Learning Engineer @ BirchTree Solutions | Providing Innovative Solutions in Military Training", "Fayetteville, North Carolina, United States", "BirchTree Solutions", "Chief Learning Engineer", "Defense & Space", L, None),
    ("Dr. Thomas McLaughlin", "Servant Leader | Learning Engineer", "Greater St. Louis", "Edward Jones", "Sr. Learning and Performance Consultant", "Financial Services", L, None),
    ("Julianne G.", "Organization Effectiveness Lead | Learning Design | ATD certified | Area9 Certified Learning Engineer", "New Albany, Indiana, United States", "Humana", "Organization Effectiveness Lead", "Insurance", L, None),
    ("John B. Costa", "CEO: RePubIT Interactive Learning | IEEE Learning Engineer | 5MoN Workflow Learning | Analytics | Digital Publishing, and DAM.", "Sanford, Florida, United States", "RePubIT Interactive Technologies", "CEO, President", "E-learning", L, None),
    ("Kristin Torrence", "AI Product Manager | Innovation Learning Engineer | Learning Science | Immersive Simulations", "Los Angeles Metropolitan Area", "Cornerstone OnDemand", "Lead Product Manager", "Computer Software", L, None),
    ("Bayar Tuvshinjargal, M.A.", "Solutions Architect | Customer Success | EdTech | Learning Engineer | Sales Engineer", "Los Angeles Metropolitan Area", "Ascend Learning", "Solutions Consultant", "E-learning", L, None),
    ("Zach Mineroff", "Assistant Director of Learning Engineering at Carnegie Mellon University", "Pittsburgh, Pennsylvania, United States", "Carnegie Mellon University", "Assistant Director of Learning Engineering", "Higher Education", L, None),
    ("Milton L. Ramirez", "EdD. MBA. Learning Engineer & Operations Strategist. Driving Performance Through Lean, AI-Enabled, and Data-Driven Learning Systems.", "Union, New Jersey, United States", "Education & Tech - Better Learning Better Leadership", "Editor & Founder", "Online Media", L, None),
    ("Nicole Trapp", "Learning Engineer | AI-Native Architect | React 19 & Next.js 16 | Strategic Learning Experience Designer", "Greater Tampa Bay Area", "University of South Florida Information Technology", "Data & UX Insights Analyst", "Higher Education", L, None),
    ("Karen CORREA", "Digital Learning Engineer", "Greater Paris Metropolitan Region", "Renault Group", "Digital Learning Engineer", "Automotive", L, None),
    ("John M. Weathers, Ph.D.", "I help organizations innovate and scale | Startup Consultant | Mentor & Coach | Board Advisor | Learning Engineer | Research & Evaluation Leader", "Chattanooga, Tennessee, United States", "Dumroo.ai | AI Ecosystem for Education", "Grant Advisor", "Higher Education", L, None),
    ("Tan Teck Xian", "Continuously Learning Engineer with a Passion for Innovation and Professional Growth | Driving Technological Advancement", "Melaka, Malacca, Malaysia", "Avient Corporation", "Application Development Engineer", "Plastics", L, NR),
    ("Faith Mundia", "Founder & CEO, FayEDU | Learning Engineer | EdTech Research | Instructional Designer | Editor, Grounding EdTech Magazine", "Nairobi County, Kenya", "FayEDU", "Chief Executive Officer", "Higher Education", L, None),
    ("Sally Aggag", "Learning Designer | Learning Engineer | TOT & CPT Trainer | Transforming Trainers into Learning Architects", "Al Asimah, Kuwait", "@sallyaggag", "Strategic Training Program Designer | TOT | CPT", "", L, None),
    ("Ahmed Gheita, CPTD", "Learning Engineer", "Egypt", "LK Studio", "Co-Founder & Board Member", "Photography", L, None),
    ("Dimitrios Sklavakis", "Learning Engineer - Ontological Engineering of Intelligent STEM Tutoring Environments", "Brussels, Brussels Region, Belgium", "European School of Brussels II", "Teacher of Mathematics and ICT", "Primary/Secondary Education", L, None),
    ("Clément R.", "Learning Engineer", "France", "CHANEL", "Learning Engineer", "Luxury Goods & Jewelry", L, None),
    ("Irene Leal de la Concha", "E-Learning Engineer at TransPerfect", "Madrid, Community of Madrid, Spain", "TransPerfect", "E-Learning Engineer", "Translation & Localization", L, None),
    ("Lamia BRIHMAT", "Instructional Designer & Adult Learning Engineer · Leadership Communication · Behavioral Change | Certified Dale Carnegie Trainer", "Le Plessis-Robinson, Île-de-France, France", "CZ", "Czarnikow Food Agent - Ingredients & Packaging", "Food & Beverages", L, None),
    ("Natalie Denmeade", "Learning Engineer and Project Manager", "Zanzibar City, Zanzibar Urban/West, Tanzania", "Moojoo Africa", "Founder and Learning Engineer", "", L, None),
    ("Madhumita Dey", "Certified Instructional Designer & Area9 Learning Engineer | Content Editor-Digital Projects | Project Manager-Books | Art of Living, breathe and meditation Teacher | International Yoga Trainer", "Germany", "", "Freelance Learning Engineer", "", L, None),
    ("Vaibhav Sharma", "Learning Engineer | Building Products that adds value", "India", "Maharshi Industries Pvt Ltd", "Project Coordinator and Design Engineer", "Industrial Automation", L, NR),
    ("Zeina Safia", "Business Analyst |MIS |Digital Learning Engineer |Data Analyst |Learning Management Systems |Visualization |Customer Lifecycle Management |HRIS Analyst | Data Management | Oracle BI | Power BI | SQL", "Dubai, United Arab Emirates", "Creative Technology Solutions", "Business System Analyst | Digital Learning Engineer", "", L, None),
]
# fmt: on


def main() -> None:
    """Load all seed records into people.json."""
    people = load_people()
    for row in _RECORDS:
        name, headline, location, company, job_title, industry, lists, triage_override = row
        rec = normalize_linkedin_pb_record(
            display_name=name,
            headline=headline,
            location=location,
            company=company,
            job_title=job_title,
            industry=industry,
            lists=lists,
            triage_override=triage_override,
            retrieved_date="2026-04-14",
        )
        people = upsert_record(rec, people)
    save_people(people)
    needs_review = sum(1 for p in people if p["triage"] == "NEEDS_REVIEW")
    print(f"Loaded {len(_RECORDS)} records. Registry: {len(people)} total, {needs_review} flagged NEEDS_REVIEW.")


if __name__ == "__main__":
    main()
