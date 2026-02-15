/* diary/static/script.js */

document.addEventListener('DOMContentLoaded', function() {
    initOrganicFlow(); 
    initCalendar();

    const textarea = document.querySelector('textarea[name="content"]');
    if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    const dateInput = document.getElementById('dateInput');
    if (dateInput && !dateInput.value) {
        dateInput.valueAsDate = new Date();
    }
});

function showLoading() {
    const textarea = document.querySelector('textarea[name="content"]');
    if (!textarea || textarea.value.trim() === "") return;

    const submitBtn = document.getElementById('submitBtn');
    const loadingBtn = document.getElementById('loadingBtn');

    submitBtn.style.display = 'none';
    loadingBtn.style.display = 'inline-block';
}

function copyToClipboard(btn) {
    const cardBody = btn.closest('.card').querySelector('.card-body');
    const text = cardBody.innerText;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerText;
        btn.innerText = "Copied";
        setTimeout(() => { btn.innerText = originalText; }, 2000);
    });
}

// --- Calendar Logic ---
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let calendarData = {}; // 儲存 { "YYYY-MM-DD": "#color" }

async function initCalendar() {
    const calendarContainer = document.getElementById('calendar-container');
    const dateInput = document.getElementById('dateInput');
    
    if (!calendarContainer || !dateInput) return;

    try {
        const response = await fetch('/api/dates');
        calendarData = await response.json();
    } catch (e) {
        console.error("Failed to fetch dates", e);
    }

    dateInput.addEventListener('change', (e) => {
        const date = new Date(e.target.value);
        if (!isNaN(date)) {
            currentYear = date.getFullYear();
            currentMonth = date.getMonth();
            renderCalendar(currentYear, currentMonth);
        }
    });

    renderCalendar(currentYear, currentMonth);
}

function renderCalendar(year, month) {
    const calendarEl = document.getElementById('calendar-grid');
    const monthYearEl = document.getElementById('calendar-month-year');
    const dateInput = document.getElementById('dateInput');
    
    if (!calendarEl || !monthYearEl) return;

    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    monthYearEl.innerText = `${monthNames[month]} ${year}`;

    calendarEl.innerHTML = '';

    const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    days.forEach(day => {
        const el = document.createElement('div');
        el.className = 'calendar-day-name';
        el.innerText = day;
        calendarEl.appendChild(el);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) {
        const el = document.createElement('div');
        el.className = 'calendar-day empty';
        calendarEl.appendChild(el);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const el = document.createElement('div');
        el.className = 'calendar-day';
        el.innerText = day;

        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        // 檢查是否有日記資料
        if (calendarData[dateStr]) {
            el.classList.add('has-entry');
            // 動態設定小圓點顏色 (使用 CSS 變數)
            el.style.setProperty('--mood-color', calendarData[dateStr]);
        } else {
            // 預設顏色
            el.style.setProperty('--mood-color', 'var(--text-main)');
        }

        if (dateInput.value === dateStr) {
            el.classList.add('selected');
        }

        el.addEventListener('click', () => {
            dateInput.value = dateStr;
            renderCalendar(year, month);
        });

        calendarEl.appendChild(el);
    }
}

window.changeMonth = function(offset) {
    currentMonth += offset;
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    } else if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    renderCalendar(currentYear, currentMonth);
};

// --- Background Animation (Organic Flow) ---
function initOrganicFlow() {
    const canvas = document.getElementById('canvas-background');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    let particles = [];
    const particleCount = 60; 
    const connectionDistance = 150;
    const flowSpeed = 0.3; 

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 1.5 + 0.5; 
            this.baseSpeedX = Math.random() * flowSpeed + 0.1;
            this.baseSpeedY = -(Math.random() * flowSpeed + 0.1);
            this.angle = Math.random() * Math.PI * 2;
            this.angleSpeed = Math.random() * 0.02;
        }
        update() {
            this.x += this.baseSpeedX + Math.sin(this.angle) * 0.2;
            this.y += this.baseSpeedY + Math.cos(this.angle) * 0.2;
            this.angle += this.angleSpeed;
            if (this.x > canvas.width + 50) this.x = -50;
            if (this.x < -50) this.x = canvas.width + 50;
            if (this.y < -50) this.y = canvas.height + 50;
            if (this.y > canvas.height + 50) this.y = -50;
        }
        draw() {
            ctx.fillStyle = 'rgba(74, 64, 54, 0.4)';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    function init() {
        particles = [];
        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }
    }
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            for (let j = i; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < connectionDistance) {
                    const opacity = (1 - distance / connectionDistance) * 0.08; 
                    ctx.strokeStyle = `rgba(74, 64, 54, ${opacity})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    init();
    animate();
}