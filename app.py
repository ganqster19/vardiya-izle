import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import calendar
from datetime import datetime

# --- SAYFA AYARLARI (Mobil Odaklı) ---
st.set_page_config(page_title="Vardiya Listesi", page_icon="📅", layout="centered")

# --- HIZLI CSS (Minimal Tasarım) ---
st.markdown("""
<style>
    /* Gereksiz boşlukları kaldır */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* Kart Tasarımı */
    .day-header {
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 5px;
        margin-top: 15px;
        margin-bottom: 5px;
        font-weight: bold;
        color: #333;
        border-left: 4px solid #ff4b4b;
    }
    .job-row {
        background-color: white;
        border-bottom: 1px solid #eee;
        padding: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .job-info { font-size: 15px; font-weight: 600; color: #000; }
    .job-sub { font-size: 12px; color: #666; margin-top: 2px; }
    
    /* İŞ TİPİ ETİKETLERİ (YENİ EKLENDİ) */
    .type-tag {
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 4px;
        display: inline-block;
        padding: 1px 4px;
        border-radius: 3px;
    }
    .tag-student { color: #1565c0; background-color: #e3f2fd; border: 1px solid #bbdefb; }
    .tag-pro { color: #e65100; background-color: #ffe0b2; border: 1px solid #ffe0b2; }

    /* Atanan Kişi Rozetleri */
    .badge-assigned { background:#f0f2f6; color:#31333F; padding:4px 8px; border-radius:6px; font-size:11px; font-weight:bold; border: 1px solid #d6d9ef; }
    .no-assign { background:#ffebee; color:#c62828; padding:2px 6px; border-radius:4px; font-size:10px; }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI (HIZLI BAĞLANTI) ---
@st.cache_resource
def get_db_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["supabase"]["host"],
            database=st.secrets["supabase"]["dbname"],
            user=st.secrets["supabase"]["user"],
            password=st.secrets["supabase"]["password"],
            port=st.secrets["supabase"]["port"],
            cursor_factory=RealDictCursor,
            sslmode='require'
        )
    except:
        st.error("Veritabanı bağlantı hatası.")
        st.stop()

# --- VERİ ÇEKME (TEK SORGU - CACHED) ---
@st.cache_data(ttl=60)
def get_month_data(month_str):
    conn = get_db_connection()
    c = conn.cursor()
    
    query = """
        SELECT 
            j.date, 
            c.name as cust_name, 
            c.location, 
            j.job_type,
            s.name as stu_name, 
            p.name as pro_name
        FROM jobs j
        JOIN customers c ON j.customer_id = c.id
        LEFT JOIN students s ON j.assigned_student_id = s.id
        LEFT JOIN professionals p ON j.assigned_pro_id = p.id
        WHERE j.date LIKE %s
        ORDER BY j.date ASC
    """
    c.execute(query, (f"%{month_str}",))
    return c.fetchall()

# --- ARAYÜZ ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("### 📅 Vardiya Listesi")
with c2:
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()

# Tarih Seçimi
now = datetime.now()
col_m, col_y = st.columns(2)
sel_m = col_m.selectbox("Ay", range(1,13), index=now.month-1, label_visibility="collapsed")
sel_y = col_y.selectbox("Yıl", [now.year, now.year+1], label_visibility="collapsed")

# Veriyi Getir
m_str = f"{sel_m:02d}.{sel_y}"
data = get_month_data(m_str)

if not data:
    st.info("Bu ay için kayıt bulunamadı.")
else:
    # Veriyi Günlere Göre Grupla
    grouped = {}
    for row in data:
        d = row['date']
        if d not in grouped: grouped[d] = []
        grouped[d].append(row)
    
    # Ekrana Bas (Sıralı)
    sorted_dates = sorted(grouped.keys(), key=lambda x: datetime.strptime(x, "%d.%m.%Y"))
    tr_days = {0:"Pazartesi", 1:"Salı", 2:"Çarşamba", 3:"Perşembe", 4:"Cuma", 5:"Cumartesi", 6:"Pazar"}

    for date_str in sorted_dates:
        # Gün Başlığı
        dt_obj = datetime.strptime(date_str, "%d.%m.%Y")
        day_name = tr_days[dt_obj.weekday()]
        
        is_today = date_str == now.strftime("%d.%m.%Y")
        today_mark = "🔴 " if is_today else ""
        
        st.markdown(f'<div class="day-header">{today_mark}{date_str} - {day_name}</div>', unsafe_allow_html=True)
        
        for job in grouped[date_str]:
            # 1. İş Tipi Etiketi (YENİ EKLENDİ)
            if job['job_type'] == 'student':
                type_html = '<span class="type-tag tag-student">🎓 ÖĞRENCİ</span>'
            else:
                type_html = '<span class="type-tag tag-pro">🛠 PROFESYONEL</span>'

            # 2. Atanan Kişi Rozeti
            if job['stu_name']:
                p_badge = f'<span class="badge-assigned">👤 {job["stu_name"]}</span>'
            elif job['pro_name']:
                p_badge = f'<span class="badge-assigned">👤 {job["pro_name"]}</span>'
            else:
                p_badge = '<span class="no-assign">Atanmadı</span>'
            
            # Kart HTML
            st.markdown(f"""
            <div class="job-row">
                <div>
                    {type_html}
                    <div class="job-info">{job['cust_name']}</div>
                    <div class="job-sub">📍 {job['location'] or '-'}</div>
                </div>
                <div style="text-align:right;">
                    {p_badge}
                </div>
            </div>
            """, unsafe_allow_html=True)
