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
      desc: "Lay down concrete foundations in algebra, geometry, and coordinates.",
      tags: ["Algebra 1 & 2", "Geometry", "Trigonometry", "Pre-Calculus"],
      icon: "📐"
    },
    {
      id: "exams",
      name: "Special Exams Prep",
      desc: "Succeed in competitive exams with custom exam boards prep kits.",
      tags: ["IGCSE", "GCSE", "WASSCE", "GCE", "JAMB", "AP Calculus", "IB Math"],
      icon: "🎓"
    },
    {
      id: "undergrad",
      name: "Undergraduate Maths",
      desc: "Rigorous higher-level math for university degrees in stem.",
      tags: ["Linear Algebra", "Calculus I-III", "Real Analysis", "Diff Equations"],
      icon: "🌌"
    }
  ],
  courses: [
    {
      id: "linear-algebra",
      sphere: "undergrad",
      title: "Linear Algebra & Matrix Theory",
      shortDesc: "Master vector spaces, linear maps, eigenvalues, and quadratic forms.",
      level: "Undergraduate",
      duration: "18 Hours",
      lectures: 24,
      materials: 8,
      rating: 4.9,
      imageIcon: "📱",
      syllabus: ["Vector Spaces & Subspaces", "Linear Independence & Bases", "Linear Transformations & Kernel", "Eigenvalues & Diagonalization", "Inner Product Spaces"]
    },
    {
      id: "ap-calculus-bc",
      sphere: "exams",
      title: "AP Calculus BC Intensive Prep",
      shortDesc: "Complete prep for the AP exam covering limits, integration techniques, and series.",
      level: "Special Exams",
      duration: "22 Hours",
      lectures: 30,
      materials: 12,
      rating: 4.8,
      imageIcon: "📈",
      syllabus: ["Limits and Continuity", "Contextual Applications of Differentiation", "Integration Techniques", "Differential Equations", "Parametric Equations & Infinite Series"]
    },
    {
      id: "igcse-extended",
      sphere: "exams",
      title: "IGCSE Extended Mathematics (0580)",
      shortDesc: "Syllabus targeted lessons covering number, algebra, shape, and probability.",
      level: "Special Exams",
      duration: "15 Hours",
      lectures: 20,
      materials: 10,
      rating: 4.7,
      imageIcon: "📐",
      syllabus: ["Numbers & Arithmetic", "Algebraic Manipulation & Graphs", "Coordinate Geometry", "Trigonometric Formulations", "Probability & Statistics Core"]
    },
    {
      id: "calculus-three",
      sphere: "undergrad",
      title: "Multivariable Calculus (Calc III)",
      shortDesc: "Dive into vector fields, double/triple integrals, Green's, and Stokes' theorems.",
      level: "Undergraduate",
      duration: "20 Hours",
      lectures: 26,
      materials: 6,
      rating: 4.9,
      imageIcon: "🌐",
      syllabus: ["Vectors & Vector Valued Functions", "Partial Derivatives", "Multiple Integrals", "Vector Calculus & Line Integrals", "Stokes & Divergence Theorems"]
    },
    {
      id: "secondary-trig",
      sphere: "secondary",
      title: "Trigonometry & Spatial Geometry",
      shortDesc: "Master angles, trigonometric ratios, sine/cosine rules, and spatial vectors.",
      level: "Secondary School",
      duration: "10 Hours",
      lectures: 14,
      materials: 5,
      rating: 4.6,
      imageIcon: "📏",
      syllabus: ["Right-Angled Triangle Trig", "The Unit Circle & Radians", "Trigonometric Graphs & Identities", "Sine and Cosine Rules", "3D Geometric Applications"]
    },
    {
      id: "ap-statistics",
      sphere: "exams",
      title: "AP Statistics Complete Guide",
      shortDesc: "Prepare for AP Statistics with comprehensive coverage of probability and inference.",
      level: "Special Exams",
      duration: "16 Hours",
      lectures: 22,
      materials: 9,
      rating: 4.8,
      imageIcon: "📊",
      syllabus: ["Exploring One and Two-Variable Data", "Collecting Data & Sampling Methods", "Probability & Random Variables", "Sampling Distributions", "Inference for Categorical & Quantitative Data"]
    },
    {
      id: "wassce-math",
      sphere: "exams",
      title: "WASSCE General Mathematics Prep",
      shortDesc: "Targeted West African Examination Council syllabus prep covering theory and multiple choice sheets.",
      level: "Special Exams",
      duration: "20 Hours",
      lectures: 25,
      materials: 15,
      rating: 4.8,
      imageIcon: "📝",
      syllabus: ["Number Bases & Modular Arithmetic", "Algebraic Fractions & Simultaneous Graphs", "Circle Geometry & Circle Coordinate Theorems", "Trigonometric Formulations & Bearings", "Probability & Standard Theory Mock Papers"]
    },
    {
      id: "jamb-math",
      sphere: "exams",
      title: "JAMB UTME Mathematics Prep",
      shortDesc: "Intensive speed-drills and shortcut strategies spanning Sets, Logarithms, Calculus and Coordinates.",
      level: "Special Exams",
      duration: "16 Hours",
      lectures: 22,
      materials: 10,
      rating: 4.9,
      imageIcon: "⚡",
      syllabus: ["Number Systems, Surds, Indices & Logarithms", "Sets, Binary Operations & Polynomials", "Differential & Integral Calculus Core", "Coordinate Geometry & Trigonometric Wave Graphs", "Speed Optimization Past Exams Solutions"]
    },
    {
      id: "gce-math",
      sphere: "exams",
      title: "GCE Advanced Level Pure Mathematics",
      shortDesc: "Advanced core theorems, trigonometric proofs, series progressions, and integral calculus for GCE A-Levels.",
      level: "Special Exams",
      duration: "24 Hours",
      lectures: 32,
      materials: 14,
      rating: 4.8,
      imageIcon: "📕",
      syllabus: ["Algebra: Partial Fractions & Binomial Expansion", "Coordinate Circles & Vector Dot Products", "Mathematical Induction & Progressions", "Advanced Integration & Volumes of Revolution", "Theoretical Proofs & Exam Marking Guides"]
    },
    {
      id: "one-on-one-intensive-stem",
      sphere: "secondary",
      title: "One-on-One Intensive STEM (Grades 4-12)",
      shortDesc: "Personalized, high-impact private instruction covering Mathematics, Physics, Chemistry, Further Mathematics, and Primary School Sciences.",
      level: "Grades 4 - 12",
      duration: "Custom Hours",
      lectures: 20,
      materials: 25,
      rating: 5.0,
      imageIcon: "👨‍🏫",
      syllabus: ["Primary School General Sciences", "Grade 4-8 Foundation Mathematics", "High School Physics & Chemistry Labs", "Further Mathematics Advanced Theory", "Customized Exam Study Guides"]
    }
  ],
  tutors: [
    {
      id: "dr-adrian",
      name: "Dr. Adrian Thorne",
      title: "PhD in Pure Mathematics",
      specialties: ["Undergrad Math", "AP Calculus BC", "Linear Algebra"],
      rating: 5.0,
      reviews: 142,
      hourlyRate: 65,
      avatar: "👨‍🏫",
      bio: "Adrian has been lecturing at universities for over 8 years. He specializes in making abstract concepts (like vector spaces and real analysis) intuitive and deeply interesting."
    },
    {
      id: "sarah-jenkins",
      name: "Sarah Jenkins, MSc",
      title: "Secondary & Exam Specialist",
      specialties: ["IGCSE", "GCSE Math", "Trigonometry", "AP Calculus AB"],
      rating: 4.9,
      reviews: 218,
      hourlyRate: 50,
      avatar: "👩‍🏫",
      bio: "Sarah is a passionate high school teacher with 10+ years of tutoring. She focuses on confidence-building and breaking down exam techniques for IGCSE and AP exams."
    },
    {
      id: "prof-marcus",
      name: "Prof. Marcus Vance",
      title: "Emeritus Math Professor",
      specialties: ["Differential Equations", "Calculus I-III", "Real Analysis"],
      rating: 5.0,
      reviews: 95,
      hourlyRate: 80,
      avatar: "👨‍💻",
      bio: "Marcus is an author of calculus textbooks. His tutoring focuses on undergraduate math prep, proving core mathematical equations, and scientific math analysis."
    }
  ],
  vault: [
    // Developer Tip: To load a real PDF, place your file in the 'assets/pdfs/' directory and match the fileUrl path.
    { id: "v1", title: "AP Calculus BC 2025 Mock Exam Pack", category: "exams", subcat: "AP MATHS", type: "PDF Bundle", size: "4.8 MB", fileUrl: "assets/pdfs/v1.pdf" },
    { id: "v2", title: "Linear Algebra Vector Spaces Cheat Sheet", category: "undergrad", subcat: "Linear Algebra", type: "Handout CheatSheet", size: "1.2 MB", fileUrl: "assets/pdfs/v2.pdf" },
    { id: "v3", title: "IGCSE Extended Math (0580) Topic-wise Past Papers", category: "exams", subcat: "IGCSE", type: "Compiled PDFs", size: "18.5 MB", fileUrl: "assets/pdfs/v3.pdf" },
    { id: "v4", title: "Calculus III Multi-Variable Integration Visual Guide", category: "undergrad", subcat: "Calculus", type: "E-Book", size: "3.5 MB", fileUrl: "assets/pdfs/v4.pdf" },
    { id: "v5", title: "GCSE Maths Higher Tier Formula Cheat Sheet", category: "exams", subcat: "GCSE", type: "One-Page PDF", size: "850 KB", fileUrl: "assets/pdfs/v5.pdf" },
    { id: "v6", title: "High School Trigonometry Identities & Proofs Workbook", category: "secondary", subcat: "Trigonometry", type: "Workbook PDF", size: "2.1 MB", fileUrl: "assets/pdfs/v6.pdf" },
    { id: "v7", title: "WASSCE General Mathematics Past Papers & Solutions Pack", category: "exams", subcat: "WASSCE", type: "Compendium PDF", size: "14.2 MB", fileUrl: "assets/pdfs/v7.pdf" },
    { id: "v8", title: "JAMB UTME Mathematics Past Question CBT Mock Pack", category: "exams", subcat: "JAMB", type: "Interactive PDF", size: "9.5 MB", fileUrl: "assets/pdfs/v8.pdf" },
    { id: "v9", title: "GCE Advanced Level Pure Maths Past Papers Bundle", category: "exams", subcat: "GCE", type: "Revision PDF", size: "16.1 MB", fileUrl: "assets/pdfs/v9.pdf" }
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
