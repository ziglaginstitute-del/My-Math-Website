/* 
  =========================================
  ZIGLAG INSTITUTE GLOBAL CLIENT-SIDE ENGINE
  =========================================
*/

// Mock Database representing all Mathematics spheres, education levels and features
const MATH_DATABASE = {
  educationLevels: [
    { id: "all", name: "All Levels", desc: "Browse complete curriculum catalog across all stages" },
    { id: "jss", name: "Junior Secondary (JSS 1–3)", desc: "Build rock-solid foundations in basic mathematics, arithmetic, and plane geometry." },
    { id: "sss", name: "Senior Secondary (SS 1–3)", desc: "Master core senior secondary algebra, trigonometry, geometry, and calculus." },
    { id: "jamb", name: "JAMB / UTME", desc: "Intensive speed-drills, shortcuts, and CBT past question mastery for university admission." },
    { id: "wassce", name: "WASSCE & NECO", desc: "Comprehensive WAEC/NECO syllabus coverage with step-by-step theory and objective derivations." },
    { id: "other", name: "Other Approved Programmes", desc: "Cambridge IGCSE, Edexcel A-Levels, Undergraduate University Mathematics, and Physics." }
  ],
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
      id: "jss-math-foundations",
      educationLevel: "jss",
      levelName: "Junior Secondary (JSS 1–3)",
      subject: "Mathematics",
      sphere: "secondary",
      title: "Junior Secondary Mathematics Foundations",
      shortDesc: "Foundational arithmetic, introductory algebra, Cartesian plane basics, and geometric constructions for JSS 1, JSS 2, and JSS 3 students.",
      level: "JSS 1–3",
      duration: "25 Hours",
      lectures: 6,
      materials: 18,
      rating: 4.9,
      imageIcon: "📐",
      counts: {
        videoLessons: 6,
        workedExamples: 18,
        interactiveExercises: 24,
        practiceQuestions: 40,
        topicAssessments: 3
      },
      learningObjectives: [
        "Master whole numbers, prime factorisation, LCM, HCF, and standard place value notation.",
        "Formulate and solve single-variable linear equations using balance techniques.",
        "Construct and measure angles, triangles, and regular polygons with precision.",
        "Calculate perimeter, surface area, and volume of compound planar shapes."
      ],
      topics: [
        {
          title: "Number & Numeration",
          subtopics: ["Whole Numbers & Place Value", "Fractions, Decimals & Percentages", "Factors, Multiples & Prime Factorisation"]
        },
        {
          title: "Basic Algebraic Processes",
          subtopics: ["Algebraic Simplification & Like Terms", "Linear Equations in One Variable", "Simple Inequalities on the Number Line"]
        },
        {
          title: "Plane Geometry & Measurement",
          subtopics: ["Angles on Parallel Lines & Polygons", "Perimeter & Area of Quadrilaterals", "Volume & Surface Area of Prisms"]
        },
        {
          title: "Everyday Statistics",
          subtopics: ["Frequency Tables & Bar Charts", "Mean, Median & Mode of Discrete Data"]
        }
      ],
      syllabus: ["Whole Numbers & Fractions", "Linear Equations & Balance Method", "Angles, Triangles & Polygons", "Mensuration of Plane Figures", "Basic Statistics & Graphs", "JSS Mastery Assessment"]
    },
    {
      id: "sss-math-core",
      educationLevel: "sss",
      levelName: "Senior Secondary (SS 1–3)",
      subject: "Mathematics",
      sphere: "secondary",
      title: "Senior Secondary Mathematics Core",
      shortDesc: "Comprehensive senior secondary syllabus covering quadratic functions, indices, logarithms, circle geometry theorems, and introductory calculus.",
      level: "SS 1–3",
      duration: "35 Hours",
      lectures: 6,
      materials: 25,
      rating: 4.9,
      imageIcon: "📊",
      counts: {
        videoLessons: 6,
        workedExamples: 24,
        interactiveExercises: 30,
        practiceQuestions: 60,
        topicAssessments: 4
      },
      learningObjectives: [
        "Solve complex quadratic equations via factorisation, completing square, and quadratic formula.",
        "Simplify multi-term surds and apply logarithm laws to exponential modeling.",
        "Prove and apply circle geometry theorems for subtended angles, cyclic quadrilaterals, and tangents.",
        "Differentiate polynomial functions from first principles and compute gradients."
      ],
      topics: [
        {
          title: "Algebraic Functions & Quadratics",
          subtopics: ["Quadratic Equations & Discriminants", "Simultaneous Linear & Quadratic Systems", "Polynomials & Remainder Theorem"]
        },
        {
          title: "Indices, Surds & Logarithms",
          subtopics: ["Laws of Indices & Equations", "Rationalising Surds & Conjugates", "Logarithmic Transformations & Bases"]
        },
        {
          title: "Circle Geometry & Trigonometry",
          subtopics: ["Circle Theorems & Cyclic Quads", "Sine & Cosine Rules", "Trigonometric Bearings & Elevations"]
        },
        {
          title: "Introductory Calculus & Vectors",
          subtopics: ["Limits & Gradients of Curves", "Differentiation of Polynomials", "2D Vectors & Dot Product"]
        }
      ],
      syllabus: ["Quadratic Functions & Graphs", "Surds, Indices & Logarithms", "Circle Geometry Theorems", "Trigonometric Bearings & Heights", "Introductory Differential Calculus", "SS Core Capstone Assessment"]
    },
    {
      id: "wassce-gce-neco-prep",
      educationLevel: "wassce",
      levelName: "WASSCE & NECO",
      subject: "Mathematics",
      sphere: "exams",
      title: "WASSCE & NECO Mathematics Mastery",
      shortDesc: "Complete WAEC and NECO syllabus coverage. Solves high-frequency past examination theory and objective questions with clear step-by-step logic.",
      level: "WASSCE",
      duration: "30 Hours",
      lectures: 6,
      materials: 22,
      rating: 4.9,
      imageIcon: "🎓",
      counts: {
        videoLessons: 6,
        workedExamples: 28,
        interactiveExercises: 36,
        practiceQuestions: 75,
        topicAssessments: 5
      },
      learningObjectives: [
        "Convert accurately between base 10 and other number bases, and solve base equations.",
        "Master algebraic fractions, simultaneous equations, and linear graph plotting.",
        "Apply geometric theorems to circle proofs and solve complex navigation bearings.",
        "Compute standard deviation, variances, and grouped frequency histograms for paper 2."
      ],
      topics: [
        {
          title: "Number Bases & Modular Arithmetic",
          subtopics: ["Base 10 Conversions & Expansions", "Operations in Base 2 (Binary)", "Modular Arithmetic & Congruence Equations"]
        },
        {
          title: "Algebraic Processes & Equations",
          subtopics: ["Algebraic Fractions & Undefined Values", "Simultaneous Equations (Elimination & Matrices)", "Linear Inequalities in Two Variables"]
        },
        {
          title: "Geometry, Bearings & Mensuration",
          subtopics: ["Circle Theorems & Tangents", "Three-figure Bearings & Elevations", "Surface Area & Volume of Spheres and Cones"]
        },
        {
          title: "Statistics & Probability",
          subtopics: ["Grouped Frequency & Cumulative Curves (Ogive)", "Standard Deviation & Variance", "Mutually Exclusive & Independent Probability"]
        }
      ],
      syllabus: ["Number Bases & Modular Arithmetic", "Algebraic Fractions & Graphs", "Circle Geometry Theorems", "Trigonometric Bearings & Heights", "Grouped Statistics & Probability", "WASSCE Past Exam Drills"]
    },
    {
      id: "utme-postutme-prep",
      educationLevel: "jamb",
      levelName: "JAMB / UTME",
      subject: "Mathematics",
      sphere: "exams",
      title: "JAMB / UTME Mathematics Speed & CBT Mastery",
      shortDesc: "Speed-drills, shortcut techniques, and pattern-recognition methods designed for high scores on the 40-question JAMB UTME Mathematics paper.",
      level: "JAMB/UTME",
      duration: "25 Hours",
      lectures: 6,
      materials: 20,
      rating: 4.9,
      imageIcon: "⚡",
      counts: {
        videoLessons: 6,
        workedExamples: 30,
        interactiveExercises: 40,
        practiceQuestions: 80,
        topicAssessments: 4
      },
      learningObjectives: [
        "Evaluate rapid speed calculations for Sets, Logarithms, Surds, and Sequences.",
        "Apply rapid differentiation and integration shortcuts for coordinate calculus problems.",
        "Determine matrix determinants, inverses, and vector cross products within 45 seconds.",
        "Develop test-taking endurance under countdown exam conditions."
      ],
      topics: [
        {
          title: "Sets, Logic & Algebra Shortcuts",
          subtopics: ["Venn Diagrams & Set Operations", "Logarithmic & Exponential Speedruns", "Sequences: AP and GP Sums to Infinity"]
        },
        {
          title: "Rapid Coordinate Geometry & Trigonometry",
          subtopics: ["Slope, Perpendicular Lines & Midpoints", "Trigonometric Identities & Values", "Equation of Circles & Radius Points"]
        },
        {
          title: "Calculus in Speed (Differentiation & Integration)",
          subtopics: ["Chain Rule & Product Rule Shortcuts", "Definite Integrals & Area Under Curves", "Maxima, Minima & Rates of Change"]
        },
        {
          title: "Matrices, Determinants & Vectors",
          subtopics: ["2x2 & 3x3 Determinants", "Matrix Inverses & Linear Systems", "Vector Magnitudes & Dot Products"]
        }
      ],
      syllabus: ["Indices, Surds & Logarithms", "Sets, Operations & Venn Diagrams", "Limits & Derivative Speedruns", "Coordinates & Trigonometric Graphs", "Matrices & 2D Vectors", "UTME CBT Timed Speed Drills"]
    },
    {
      id: "other-exams-prep",
      educationLevel: "other",
      levelName: "Other Approved Programmes",
      subject: "Mathematics",
      sphere: "exams",
      title: "International Curricula (Cambridge IGCSE & Edexcel A-Levels)",
      shortDesc: "Targeted modules mapped to Cambridge IGCSE (0580), Edexcel International A-Level, and Oxford AQA syllabus specifications.",
      level: "Other Programmes",
      duration: "35 Hours",
      lectures: 4,
      materials: 25,
      rating: 4.9,
      imageIcon: "🌍",
      counts: {
        videoLessons: 4,
        workedExamples: 20,
        interactiveExercises: 25,
        practiceQuestions: 50,
        topicAssessments: 3
      },
      learningObjectives: [
        "Master Cambridge IGCSE extended algebra, geometric vectors, and probability trees.",
        "Perform rigorous mathematical proof by induction and contradiction for A-Levels.",
        "Compute partial fraction decomposition and integrate rational functions.",
        "Solve 3D vector geometry problems involving planes and skew lines."
      ],
      topics: [
        {
          title: "IGCSE Extended Core",
          subtopics: ["Algebraic Fractions & Graphs of Functions", "Probability Trees & Combined Events", "Transformations & Matrix Operators"]
        },
        {
          title: "Edexcel & Cambridge Pure Mathematics",
          subtopics: ["Proof by Induction & Direct Methods", "Binomial Expansion for Any Rational Index", "Integration by Parts & Substitution"]
        },
        {
          title: "3D Vectors & Mechanics Basics",
          subtopics: ["Vectors in 3-Dimensional Space", "Dot Product & Angles Between Vectors"]
        }
      ],
      syllabus: ["Cambridge IGCSE Extended Core", "Edexcel International A-Levels", "AQA GCSE Mathematics", "IB Math Analysis & Approaches"]
    },
    {
      id: "undergrad-math-courses",
      educationLevel: "other",
      levelName: "Other Approved Programmes",
      subject: "Mathematics",
      sphere: "undergrad",
      title: "Undergraduate University Mathematics",
      shortDesc: "University-level linear algebra, multivariable calculus, and real analysis tailored for STEM students, engineering majors, and aspiring researchers.",
      level: "Undergraduate",
      duration: "40 Hours",
      lectures: 4,
      materials: 30,
      rating: 5.0,
      imageIcon: "🌌",
      counts: {
        videoLessons: 4,
        workedExamples: 16,
        interactiveExercises: 20,
        practiceQuestions: 35,
        topicAssessments: 3
      },
      learningObjectives: [
        "Prove subspace properties, linear independence, spanning sets, and basis dimensions.",
        "Compute eigenvalues, eigenvectors, and perform matrix diagonalization.",
        "Calculate directional derivatives, gradients, and solve Lagrange multipliers in 3D.",
        "Evaluate double and triple integrals over arbitrary non-rectangular regions."
      ],
      topics: [
        {
          title: "Linear Algebra & Vector Spaces",
          subtopics: ["Vector Spaces & Subspace Axioms", "Linear Independence, Spans & Bases", "Eigenvalues, Eigenvectors & Diagonalization"]
        },
        {
          title: "Multivariable Advanced Calculus",
          subtopics: ["Partial Derivatives & Chain Rule in R^n", "Gradient Vectors & Tangent Planes", "Double & Triple Integrals with Polar Transformations"]
        },
        {
          title: "Differential Equations & Modeling",
          subtopics: ["First-Order Separable & Exact ODEs", "Second-Order Homogeneous Linear Systems"]
        }
      ],
      syllabus: ["Linear Algebra & Matrix Theory", "Calculus III Multivariable Analysis", "Introduction to Real Analysis", "Differential Equations & Proofs"]
    },
    {
      id: "extras-general-videos",
      educationLevel: "other",
      levelName: "Other Approved Programmes",
      subject: "General STEM",
      sphere: "secondary",
      title: "Curiosity & Advanced STEM Showcase",
      shortDesc: "Deep-dive mathematical derivations, Olympiad problem puzzles, historical proofs, and whiteboard masterclasses by Mr. Isaac Olusola.",
      level: "General STEM",
      duration: "Flexible",
      lectures: 4,
      materials: 10,
      rating: 4.8,
      imageIcon: "📺",
      counts: {
        videoLessons: 4,
        workedExamples: 12,
        interactiveExercises: 15,
        practiceQuestions: 25,
        topicAssessments: 2
      },
      learningObjectives: [
        "Explore creative Olympiad-style mathematical problem-solving strategies.",
        "Understand De Moivre's theorem and complex exponential proofs.",
        "Evaluate advanced limit problems involving factorials and Gamma functions."
      ],
      topics: [
        {
          title: "Whiteboard Masterclasses",
          subtopics: ["Advanced Factorial Limits", "De Moivre's Proofs & Trigonometric Identites", "History of Mathematical Notation"]
        }
      ],
      syllabus: ["Whiteboard Showcase Sessions", "Mathematics History & Curiosities", "General Study & Memory Tricks", "Showcase Renders Walkthroughs"]
    },
    {
      id: "wassce-gce-neco-physics",
      educationLevel: "wassce",
      levelName: "WASSCE & NECO",
      subject: "Physics",
      sphere: "exams",
      title: "WASSCE & NECO Physics Preparation",
      shortDesc: "Complete West African physics syllabus covering mechanics, thermal physics, wave motion, electricity, and practical experimental techniques.",
      level: "WASSCE",
      duration: "30 Hours",
      lectures: 6,
      materials: 25,
      rating: 4.9,
      imageIcon: "⚡",
      counts: {
        videoLessons: 6,
        workedExamples: 24,
        interactiveExercises: 30,
        practiceQuestions: 60,
        topicAssessments: 4
      },
      learningObjectives: [
        "Solve complex kinematics, projectile motion, and circular motion calculations.",
        "Apply thermodynamic laws, heat capacity formulas, and gas laws.",
        "Calculate resistance, electromotive force, and power in electrical circuits.",
        "Analyse wave properties, resonance in air columns, and lens refraction."
      ],
      topics: [
        {
          title: "Mechanics & Properties of Matter",
          subtopics: ["Equations of Motion & Projectiles", "Newton's Laws & Momentum Conservation", "Work, Energy & Power Efficiencies"]
        },
        {
          title: "Thermal Physics & Waves",
          subtopics: ["Specific Heat Capacity & Latent Heat", "Gas Laws (Boyle, Charles, Ideal)", "Wave Propagation, Sound & Resonance"]
        },
        {
          title: "Electricity, Magnetism & Atomic Physics",
          subtopics: ["Ohm's Law & Kirchhoff's Rules", "Magnetic Fields & Electromagnetic Induction", "Radioactive Decay & Half-Life"]
        }
      ],
      syllabus: ["Mechanics & Properties of Matter", "Waves & Sound Vibrations", "Heat Energy & Thermodynamics", "Electricity, Magnetism & Modern Physics"]
    },
    {
      id: "utme-postutme-physics",
      educationLevel: "jamb",
      levelName: "JAMB / UTME",
      subject: "Physics",
      sphere: "exams",
      title: "JAMB / UTME Physics Speed & CBT Mastery",
      shortDesc: "Targeted 40-question UTME physics speed-run strategies, key formula memorisation aids, and fast numerical calculation shortcuts.",
      level: "JAMB/UTME",
      duration: "25 Hours",
      lectures: 6,
      materials: 20,
      rating: 4.8,
      imageIcon: "🔌",
      counts: {
        videoLessons: 6,
        workedExamples: 25,
        interactiveExercises: 35,
        practiceQuestions: 70,
        topicAssessments: 4
      },
      learningObjectives: [
        "Rapidly compute projectile velocity components and flight times under 60 seconds.",
        "Solve resistor combinations and electric circuit voltage drops without scrap paper.",
        "Apply mirror and thin lens formulas to predict real vs virtual image distances."
      ],
      topics: [
        {
          title: "Mechanics & Dynamics Drills",
          subtopics: ["Scalars, Vectors & Motion Graphs", "Forces, Friction & Equilibrium"]
        },
        {
          title: "Optics & Electricity Shortcuts",
          subtopics: ["Refraction, Lenses & Snell's Law", "Electric Fields, Potential & Capacitance"]
        }
      ],
      syllabus: ["Scalars, Vectors & Motion Equations", "Forces, Work, Energy & Power", "Thermodynamics & Gas Properties", "Electric Fields & Nuclear Physics"]
    },
    {
      id: "other-exams-physics",
      educationLevel: "other",
      levelName: "Other Approved Programmes",
      subject: "Physics",
      sphere: "exams",
      title: "International Physics (IGCSE & A-Levels)",
      shortDesc: "Cambridge IGCSE Physics and Edexcel/AQA International A-Level Physics modules with rigorous calculus-based mechanics and fields.",
      level: "Other Programmes",
      duration: "35 Hours",
      lectures: 4,
      materials: 30,
      rating: 4.9,
      imageIcon: "⚛️",
      counts: {
        videoLessons: 4,
        workedExamples: 18,
        interactiveExercises: 22,
        practiceQuestions: 45,
        topicAssessments: 3
      },
      learningObjectives: [
        "Master Hooke's law, elastic potential energy, and rotational dynamics.",
        "Calculate gravitational field strengths, orbital speeds, and escape velocities.",
        "Analyse photoelectric emission, de Broglie wavelengths, and line spectra."
      ],
      topics: [
        {
          title: "Cambridge IGCSE & A-Level Core",
          subtopics: ["Forces & Momentum", "Gravitational & Electric Fields", "Quantum & Nuclear Physics"]
        }
      ],
      syllabus: ["Cambridge IGCSE Physics Core", "Edexcel International A-Level Mechanics", "AQA GCSE Physics Studies", "OCR A-Level Physics & Practical Skills"]
    }
  ],
  tutors: [
    {
      id: "Isaac Olusola",
      name: "Mr. Isaac Olusola",
      title: "MSc in Applied Mathematics",
      specialties: ["Junior & Senior Secondary Math", "Undergraduate Higher Math", "WASSCE & JAMB Prep"],
      rating: 5.0,
      reviews: 142,
      hourlyRate: 50,
      avatar: "assets/isaac_olusola_avatar.webp",
      bio: "Isaac has been teaching mathematics for over 5 years. He specializes in making mathematical concepts (like vectors and calculus) intuitive, visual, and deeply interesting."
    }
  ],
  vault: [
    { id: "v1", title: "Number Bases Comprehensive Lecture Notes", category: "exams", subcat: "WASSCE/JAMB", type: "PDF Bundle", size: "400 KB", fileUrl: "https://drive.google.com/file/d/1fGZITEA9sjVcHpxc-imo2eJKcHRQM1S-/view?usp=drive_link" }
  ]
};

// =========================================
// CLIENT STATE ENGINE (LOCAL PERSISTENCE)
// =========================================
const AppState = {
  theme: localStorage.getItem("theme") || "light",
  bookings: JSON.parse(localStorage.getItem("bookings")) || [],
  completedLessons: JSON.parse(localStorage.getItem("completedLessons")) || {},
  recentLessons: JSON.parse(localStorage.getItem("recentLessons")) || [],
  xp: parseInt(localStorage.getItem("studentXP")) || 120,
  streak: parseInt(localStorage.getItem("studyStreak")) || 3,
  
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
    let didComplete = false;
    if (index > -1) {
      this.completedLessons[courseId].splice(index, 1);
      this.xp = Math.max(0, this.xp - 50);
    } else {
      this.completedLessons[courseId].push(lessonId);
      this.xp += 50;
      didComplete = true;
    }
    localStorage.setItem("completedLessons", JSON.stringify(this.completedLessons));
    localStorage.setItem("studentXP", this.xp.toString());
    
    // Dispatch custom event for UI updates
    window.dispatchEvent(new CustomEvent("lessonProgressChanged", {
      detail: { courseId, lessonId, didComplete, completedCount: this.getCompletedCount(courseId) }
    }));
    
    return didComplete;
  },

  isLessonComplete(courseId, lessonId) {
    return (this.completedLessons[courseId] || []).includes(lessonId);
  },

  getCompletedCount(courseId) {
    return (this.completedLessons[courseId] || []).length;
  },

  recordRecentLesson(courseId, lessonIndex, title) {
    this.recentLessons = this.recentLessons.filter(r => !(r.courseId === courseId && r.lessonIndex === lessonIndex));
    this.recentLessons.unshift({
      courseId,
      lessonIndex,
      title,
      timestamp: Date.now()
    });
    if (this.recentLessons.length > 6) {
      this.recentLessons.pop();
    }
    localStorage.setItem("recentLessons", JSON.stringify(this.recentLessons));
  },

  awardXP(amount) {
    this.xp += amount;
    localStorage.setItem("studentXP", this.xp.toString());
    return this.xp;
  }
};


document.addEventListener("DOMContentLoaded", () => {
  AppState.applyTheme();
  
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => AppState.toggleTheme());
  }

  // Mobile Navigation Drawer Toggle
  initMobileNavigation();
  
  // Custom micro-interaction: Add float math symbols inside heroes
  initFloatingSymbols();

  // Discreet Owner Access triggers (hidden from public visitors)
  initDiscreetAdminAccess();
});

// Mobile Navigation Toggle Handler
function initMobileNavigation() {
  const navbar = document.querySelector(".navbar");
  const navLinks = document.querySelector(".nav-links");
  if (!navbar || !navLinks) return;

  // Check if mobile button already exists or create one
  let toggleBtn = navbar.querySelector(".mobile-nav-toggle");
  if (!toggleBtn) {
    toggleBtn = document.createElement("button");
    toggleBtn.className = "mobile-nav-toggle";
    toggleBtn.setAttribute("aria-label", "Toggle navigation menu");
    toggleBtn.innerHTML = "☰";
    navbar.insertBefore(toggleBtn, navLinks);
  }

  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = navLinks.classList.toggle("is-open");
    toggleBtn.innerHTML = isOpen ? "✕" : "☰";
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (!navbar.contains(e.target)) {
      navLinks.classList.remove("is-open");
      toggleBtn.innerHTML = "☰";
    }
  });

  // Close when a link inside mobile drawer is clicked
  navLinks.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("is-open");
      toggleBtn.innerHTML = "☰";
    });
  });
}

// Discreet Owner Access triggers for the portal administrator
function initDiscreetAdminAccess() {
  // 1. Keyboard Shortcut: Ctrl + Shift + A or Alt + A
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey && e.shiftKey && (e.key === "A" || e.key === "a")) || (e.altKey && (e.key === "a" || e.key === "A"))) {
      e.preventDefault();
      window.location.href = "admin.html";
    }
  });

  // 2. Secret Triple-Click on Header Logo
  const logos = document.querySelectorAll(".logo, .logo-container, .logo-img");
  logos.forEach(logo => {
    let count = 0;
    let timer = null;
    logo.addEventListener("click", (e) => {
      count++;
      if (count === 3) {
        e.preventDefault();
        window.location.href = "admin.html";
      }
      clearTimeout(timer);
      timer = setTimeout(() => { count = 0; }, 1200);
    });
  });

  // 3. Secret Triple-Click on Footer Copyright Area
  const footerElements = document.querySelectorAll("footer p, .footer-bottom, .footer-content");
  footerElements.forEach(el => {
    let count = 0;
    let timer = null;
    el.addEventListener("click", () => {
      count++;
      if (count === 3) {
        window.location.href = "admin.html";
      }
      clearTimeout(timer);
      timer = setTimeout(() => { count = 0; }, 1200);
    });
  });
}

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
