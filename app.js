/* 
  =========================================
  ZIGLAG INSTITUTE GLOBAL CLIENT-SIDE ENGINE
  =========================================
*/

// Mock Database representing all Mathematics spheres and features
const MATH_DATABASE = {
  spheres: [
    {
      id: "secondary",
      name: "Secondary School Maths",
      desc: "Lay down concrete foundations in algebra, geometry, coordinates, and general science.",
      tags: ["Grade 4 - 12", "Algebra 1 & 2", "Geometry", "Trigonometry", "Pre-Calculus"],
      icon: "📐"
    },
    {
      id: "exams",
      name: "Special Exams Prep",
      desc: "Succeed in competitive exams with custom exam boards prep kits.",
      tags: ["IGCSE", "GCSE", "WASSCE", "GCE", "UTME/POST UTME", "NECO"],
      icon: "🎓"
    },
    {
      id: "undergrad",
      name: "Undergraduate Maths",
      desc: "Rigorous higher-level math for university degrees in stem.",
      tags: ["Linear Algebra", "Calculus I-III", "Mathematical Methods", "Diff Equations(Ordinary and Partial)", "Mathematical Modelling"],
      icon: "🌌"
    }
  ],
  courses: [
    {
      id: "wassce-gce-neco-prep",
      sphere: "exams",
      title: "WASSCE/GCE/NECO Preparation",
      shortDesc: "Exam-focused prep covering the complete WAEC/GCE/NECO syllabus with theory and objective past questions solved.",
      level: "Special Exams",
      duration: "30 Hours",
      lectures: 6,
      materials: 20,
      rating: 4.8,
      imageIcon: "🎓",
      syllabus: ["Number Bases & Modular Arithmetic", "Algebraic Fractions & Graphs", "Circle Geometry Theorems", "Trigonometric Bearings & Heights"]
    },
    {
      id: "utme-postutme-prep",
      sphere: "exams",
      title: "UTME/POST UTME Preparation",
      shortDesc: "Intensive speed-drills and shortcut strategies spanning Sets, Logarithms, Calculus, and Coordinates for UTME/POST UTME.",
      level: "Special Exams",
      duration: "25 Hours",
      lectures: 6,
      materials: 18,
      rating: 4.9,
      imageIcon: "⚡",
      syllabus: ["Indices, Surds & Logarithms", "Sets, Operations & Venn Diagrams", "Limits & Derivative Speedruns", "Coordinates & Trigonometric Graphs"]
    },
    {
      id: "other-exams-prep",
      sphere: "exams",
      title: "Other Exam Body Preparation (GCSE, A-Level, IGCSE)",
      shortDesc: "Targeted prep covering international syllabus standards for Cambridge, Edexcel, and AQA.",
      level: "Special Exams",
      duration: "35 Hours",
      lectures: 4,
      materials: 25,
      rating: 4.9,
      imageIcon: "🌍",
      syllabus: ["Cambridge IGCSE Extended Core", "Edexcel International A-Levels", "AQA GCSE Mathematics", "IB Math Analysis & Approaches"]
    },
    {
      id: "undergrad-math-courses",
      sphere: "undergrad",
      title: "Undergraduate Math Courses",
      shortDesc: "Rigorous advanced university courses spanning linear algebra, multivariable calculus, and real analysis.",
      level: "Undergraduate",
      duration: "40 Hours",
      lectures: 4,
      materials: 30,
      rating: 5.0,
      imageIcon: "🌌",
      syllabus: ["Linear Algebra & Matrix Theory", "Calculus III Multivariable Analysis", "Introduction to Real Analysis", "Differential Equations & Proofs"]
    },
    {
      id: "extras-general-videos",
      sphere: "secondary",
      title: "Extras (General Videos)",
      shortDesc: "Enrichment lectures, general interest math puzzles, study tips, and showcase renders.",
      level: "General",
      duration: "Flexible",
      lectures: 4,
      materials: 10,
      rating: 4.8,
      imageIcon: "📺",
      syllabus: ["Whiteboard Showcase Sessions", "Mathematics History & Curiosities", "General Study & Memory Tricks", "Showcase Renders Walkthroughs"]
    },
    {
      id: "wassce-gce-neco-physics",
      sphere: "exams",
      title: "WASSCE/GCE/NECO Preparation Physics",
      shortDesc: "Exam preparation covering West African physics concepts, mechanics, electricity, waves, and practical mock guides.",
      level: "Special Exams",
      duration: "30 Hours",
      lectures: 6,
      materials: 25,
      rating: 4.9,
      imageIcon: "⚡",
      syllabus: ["Mechanics & Properties of Matter", "Waves & Sound Vibrations", "Heat Energy & Thermodynamics", "Electricity, Magnetism & Modern Physics"]
    },
    {
      id: "utme-postutme-physics",
      sphere: "exams",
      title: "UTME/POST UTME Preparation Physics",
      shortDesc: "UTME physics syllabus prep featuring rapid speed-run practice papers, formulas, and shortcut tricks.",
      level: "Special Exams",
      duration: "25 Hours",
      lectures: 6,
      materials: 20,
      rating: 4.8,
      imageIcon: "🔌",
      syllabus: ["Scalars, Vectors & Motion Equations", "Forces, Work, Energy & Power", "Thermodynamics & Gas Properties", "Electric Fields & Nuclear Physics"]
    },
    {
      id: "other-exams-physics",
      sphere: "exams",
      title: "Other Exam Body Preparation (GCSE, A-Level, IGCSE) Physics",
      shortDesc: "International physics exam preparation focusing on Cambridge, Edexcel, OCR and AQA assessment modules.",
      level: "Special Exams",
      duration: "35 Hours",
      lectures: 4,
      materials: 30,
      rating: 4.9,
      imageIcon: "⚛️",
      syllabus: ["Cambridge IGCSE Physics Core", "Edexcel International A-Level Mechanics", "AQA GCSE Physics Studies", "OCR A-Level Physics & Practical Skills", "AQA A-Level Physics & Practical Skills"]
    }
  ],
  tutors: [
    {
      id: "Isaac Olusola",
      name: "Mr. Isaac Olusola",
      title: "MSc in Applied Mathematics",
      specialties: ["Secondary school Math", "Undergraduate Math", "Exam Prep"],
      rating: 5.0,
      reviews: 142,
      hourlyRate: 50,
      avatar: "👨‍🏫",
      bio: "Isaac has been teaching mathematics for over 5 years. He specializes in making mathematical concepts (like vectors and calculus) intuitive and deeply interesting."
    },
  ],
  vault: [
    // Developer Tip: To load a real PDF, place your file in the 'assets/pdfs/' directory and match the fileUrl path.
    { id: "v1", title: "Number Bases Note", category: "exams", subcat: "WASSCE/JAMB", type: "PDF Bundle", size: "400 KB", fileUrl: "https://drive.google.com/file/d/1fGZITEA9sjVcHpxc-imo2eJKcHRQM1S-/view?usp=drive_link" }
  ]
};

// =========================================
// CLIENT STATE ENGINE
// =========================================
const AppState = {
  theme: localStorage.getItem("theme") || "dark",
  bookings: JSON.parse(localStorage.getItem("bookings")) || [],
  completedLessons: JSON.parse(localStorage.getItem("completedLessons")) || {},
  
  toggleTheme() {
    this.theme = this.theme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", this.theme);
    this.applyTheme();
  },
  
  applyTheme() {
    document.documentElement.setAttribute("data-theme", this.theme);
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.innerHTML = this.theme === "dark" ? "☀️" : "🌙";
    }
  },

  addBooking(booking) {
    this.bookings.push(booking);
    localStorage.setItem("bookings", JSON.stringify(this.bookings));
  },

  toggleLessonComplete(courseId, lessonId) {
    if (!this.completedLessons[courseId]) {
      this.completedLessons[courseId] = [];
    }
    const index = this.completedLessons[courseId].indexOf(lessonId);
    if (index > -1) {
      this.completedLessons[courseId].splice(index, 1);
    } else {
      this.completedLessons[courseId].push(lessonId);
    }
    localStorage.setItem("completedLessons", JSON.stringify(this.completedLessons));
    return this.completedLessons[courseId].includes(lessonId);
  },

  getCompletedCount(courseId) {
    return (this.completedLessons[courseId] || []).length;
  }
};

// =========================================
// INITIALIZER SETUP
// =========================================
document.addEventListener("DOMContentLoaded", () => {
  AppState.applyTheme();
  
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => AppState.toggleTheme());
  }
  
  // Custom micro-interaction: Add float math symbols inside heroes
  initFloatingSymbols();
});

// Creative detail: Floating mathematical glyphs in dashboard background
function initFloatingSymbols() {
  const heroVisual = document.querySelector('.hero-visual');
  if (!heroVisual) return;
  
  const symbols = ['∫', '√', 'π', 'Σ', '∞', 'Δ', 'λ', 'θ', '≈', 'f(x)'];
  for (let i = 0; i < 6; i++) {
    const orb = document.createElement('div');
    orb.innerText = symbols[Math.floor(Math.random() * symbols.length)];
    orb.style.position = 'absolute';
    orb.style.fontSize = `${Math.floor(Math.random() * 20) + 18}px`;
    orb.style.fontWeight = 'bold';
    orb.style.color = i % 2 === 0 ? 'var(--primary-color)' : 'var(--secondary-color)';
    orb.style.opacity = '0.35';
    orb.style.top = `${Math.random() * 80 + 10}%`;
    orb.style.left = `${Math.random() * 80 + 10}%`;
    orb.style.transform = `rotate(${Math.random() * 360}deg)`;
    orb.style.pointerEvents = 'none';
    orb.style.animation = `float-slow-${i} ${Math.floor(Math.random() * 5) + 6}s infinite ease-in-out alternate`;
    
    // Inject dynamic style rule for floating animations
    const keyframes = `
      @keyframes float-slow-${i} {
        0% { transform: translateY(0px) rotate(0deg) scale(1); }
        100% { transform: translateY(${Math.random() * 30 - 15}px) rotate(${Math.random() * 60 - 30}deg) scale(1.1); }
      }
    `;
    const styleEl = document.createElement('style');
    styleEl.textContent = keyframes;
    document.head.appendChild(styleEl);
    heroVisual.appendChild(orb);
  }
}
