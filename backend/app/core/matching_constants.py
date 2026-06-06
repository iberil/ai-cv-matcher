# Critical Skills - SIRALAMA ÖNEMLİ: Spesifikten Genele!
CRITICAL_SKILLS = {
    '.NET Developer': {
        'keywords': ['.net developer', 'dotnet developer', 'c# developer', 'asp.net'],
        'required': ['.net', 'c#', 'dotnet', 'asp.net', 'csharp'],
        'penalty': -70
    },
    'Java Developer': {
        'keywords': ['java developer', 'java engineer', 'spring developer'],
        'required': ['java', 'spring', 'hibernate', 'jvm'],
        'penalty': -70
    },
    'Data Engineer': {
        'keywords': ['data engineer', 'veri mühendisi', 'veri mühendis', 'data scientist', 'veri bilimci', 'veri analiz', 'snowflake engineer', 'dbt developer'],
        'required': ['python', 'sql', 'etl', 'snowflake', 'dbt', 'airflow', 'spark', 'kafka', 'databricks'],
        'penalty': -60
    },
    'Frontend Developer': {
        'keywords': ['frontend developer', 'front-end developer', 'ön yüz geliştirici', 'ui/ux developer'],
        'required': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'typescript'],
        'penalty': -50
    },
    'Backend Developer': {
        'keywords': ['backend developer', 'back-end developer', 'arka uç geliştirici', 'server developer'],
        'required': ['spring boot', 'django', 'fastapi', 'express', 'laravel', 'flask'],
        'penalty': -70
    },
    'Mobile Developer': {
        'keywords': ['mobile developer', 'ios developer', 'android developer', 'mobil geliştirici'],
        'required': ['swift', 'kotlin', 'java', 'react native', 'flutter', 'ios', 'android'],
        'penalty': -60
    },
    'ETL Developer': {
        'keywords': ['etl developer', 'etl engineer', 'data integration', 'data warehouse engineer'],
        'required': ['etl', 'ssis', 'talend', 'informatica', 'pentaho', 'python etl', 'spark etl', 'liquibase', 'dbt', 'snowflake'],
        'penalty': -60
    },
    'DevOps': {
        'keywords': ['devops', 'sre', 'infrastructure engineer', 'altyapı mühendis'],
        'required': ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'jenkins', 'ci/cd'],
        'penalty': -50
    },
    'Developer': {
        'keywords': ['software developer', 'software engineer', 'yazılım geliştirici', 'yazılım mühendis'],
        'required': ['python', 'java', 'c#', '.net', 'javascript', 'react', 'angular', 'swift', 'kotlin', 'php', 'sql', 'git'],
        'penalty': -50
    },
    'Avukat': {
        'keywords': ['avukat', 'lawyer', 'legal', 'hukuk'],
        'required': [],
        'penalty': -100
    },
    'Non-Tech': {
        'keywords': ['doktor', 'hemşire', 'muhasebe', 'mimar', 'doctor', 'nurse', 'accounting', 'architect'],
        'required': [],
        'penalty': -100
    }
}

# Teknik işler için anahtar kelimeler
TECH_JOB_KEYWORDS = [
    'software developer', 'yazılım geliştirici', 'programmer',
    'software engineer', 'yazılım mühendisi', 'backend developer', 'frontend developer',
    'full stack', 'python developer', 'java developer', '.net developer',
    'android developer', 'ios developer', 'mobile developer',
    'data engineer', 'veri mühendisi', 'etl developer', 'devops engineer',
    'system administrator', 'network engineer', 'database administrator'
]

# Teknik olmayan eğitim alanları (VETO listesi)
NON_TECH_EDUCATION_KEYWORDS = [
    'political science', 'politics', 'siyaset bilimi', 'law', 'hukuk',
    'business administration', 'işletme', 'economics', 'iktisat',
    'psychology', 'psikoloji', 'sociology', 'sosyoloji',
    'literature', 'edebiyat', 'history', 'tarih', 'philosophy',
    'felsefe', 'fine arts', 'güzel sanatlar', 'music', 'müzik',
    'theology', 'ilahiyat', 'medicine', 'tıp',
    'nursing', 'hemşirelik', 'pharmacy', 'eczacılık',
    'liberal arts', 'humanities', 'beşeri bilimler'
]

# Teknik eğitim alanları
TECH_EDUCATION_KEYWORDS = [
    'computer science', 'bilgisayar mühendisliği', 'software engineering',
    'yazılım mühendisliği', 'electrical engineering', 'elektrik mühendisliği',
    'industrial engineering', 'endüstri mühendisliği', 'mathematics',
    'matematik', 'physics', 'fizik', 'engineering', 'mühendislik',
    'information technology', 'bilgi teknolojileri', 'computer engineering',
    'bilgisayar mühendisi', 'management information systems', 'mis'
]

# --- CV Service Constants ---

SKILLS_KEYWORDS = [
    # Programlama
    'python', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
    'javascript', 'typescript', 'html', 'css', 'sql', 'r',
    # Framework / Kütüphane
    'react', 'angular', 'vue', 'next.js', 'node.js', 'django', 'flask', 'fastapi',
    'spring', 'laravel', 'express', 'tensorflow', 'pytorch', 'pandas', 'numpy',
    # DevOps / Cloud
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'git',
    'linux', 'ci/cd', 'ansible',
    # Veritabanı / Veri Mühendisliği
    'mongodb', 'postgresql', 'mysql', 'oracle', 'redis', 'elasticsearch', 
    'snowflake', 'snowpark', 'dbt', 'apache airflow', 'airflow', 'informatica', 
    'liquibase', 'monte carlo', 'data observability', 'observability', 
    'kafka', 'databricks', 'spark', 'apache spark', 'pyspark', 'hadoop', 
    'bigquery', 'redshift', 'clickhouse', 'scylla', 'cassandra', 'teradata', 
    'etl', 'data warehousing', 'data lake', 'dwh', 'data science',
    # Mühendislik
    'autocad', 'solidworks', 'cad', 'matlab', 'ansys', 'plc', 'sap',
    'labview', 'mechanical', 'electrical', 'hydraulic', 'fabrication',
    # Metodoloji
    'agile', 'scrum', 'lean', 'six sigma', 'quality assurance', 'testing',
    # Ofis / Genel
    'ms office', 'excel', 'powerpoint', 'visio', 'jira', 'confluence',
    # Dijital Pazarlama
    'seo', 'sem', 'google analytics', 'google ads', 'facebook ads',
    'search engine optimization', 'search engine marketing',
    'social media marketing', 'social media', 'content marketing',
    'email marketing', 'hubspot', 'salesforce', 'mailchimp', 'hootsuite',
    'copywriting', 'content strategy', 'content creation',
    'digital marketing', 'affiliate marketing', 'ppc', 'cro',
    'a/b testing', 'marketing automation', 'crm',
    # Tasarım
    'photoshop', 'illustrator', 'figma', 'sketch', 'canva', 'indesign',
    'adobe', 'ui/ux', 'graphic design', 'video editing', 'after effects',
    # Analitik / BI
    'tableau', 'power bi', 'google data studio', 'looker', 'mixpanel',
    'data analysis', 'data visualization', 'market research',
    # Yazma / İletişim
    'editing', 'proofreading', 'blogging', 'journalism', 'public relations',
    'communication', 'presentation', 'collaboration',
    # Finans / Muhasebe
    'accounting', 'bookkeeping', 'financial analysis', 'budgeting', 'quickbooks',
    # Proje Yönetimi
    'project management', 'product management', 'stakeholder management',
    'risk management', 'pmp',
]

JOB_TITLE_KEYWORDS = [
    'engineer', 'technician', 'director', 'manager', 'specialist', 'analyst',
    'supervisor', 'intern', 'lead', 'developer', 'consultant', 'officer', 'assistant',
    'journeyman', 'coordinator', 'mechanic', 'planner', 'superintendent'
]

EDUCATION_KEYWORDS = [
    'university', 'college', 'institute', 'bachelor', 'master', 'phd', 'associate', 'diploma'
]

NEGATIVE_KEYWORDS = [
    'city', 'state', 'name', 'skills', 'education', 'experience', 'profile', 'summary',
    'company', 'work', 'history', 'training', 'professional', 'personal', 'information',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
    'october', 'november', 'december', 'current', 'inc', 'llc', 'corp'
]

# --- Job Analysis Service Constants ---

JOB_EDUCATION_PATTERNS = {
    'engineering': [
        r'mühendislik\s*(mezunu|diploması|eğitimi)',
        r'engineering\s*(degree|graduate)',
        r'teknik\s*üniversite',
        r'fen\s*bilimleri',
        r'mühendis\s*olma'
    ],
    'business': [
        r'işletme\s*(mezunu|diploması)',
        r'business\s*(degree|administration)',
        r'iktisat\s*(mezunu|diploması)',
        r'economics\s*degree'
    ],
    'computer_science': [
        r'bilgisayar\s*mühendisliği',
        r'computer\s*(science|engineering)',
        r'yazılım\s*mühendisliği',
        r'software\s*engineering'
    ]
}

JOB_EXPERIENCE_PATTERNS = {
    'entry': [r'0-2\s*yıl', r'entry\s*level', r'junior', r'yeni\s*mezun'],
    'mid': [r'2-5\s*yıl', r'3-5\s*yıl', r'mid\s*level', r'orta\s*seviye'],
    'senior': [r'5\+\s*yıl', r'senior', r'uzman', r'lead', r'architect']
}

JOB_TECH_SKILLS = {
    'programming': ['python', 'java', 'c#', 'javascript', 'php', 'go', 'rust'],
    'frontend': ['react', 'angular', 'vue', 'html', 'css', 'typescript'],
    'backend': ['django', 'spring', 'asp.net', 'node.js', 'fastapi'],
    'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
    'mobile': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin']
}
