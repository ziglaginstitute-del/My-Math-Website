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
// ============================================================================
// CENTRAL AUTHENTICATED API CLIENT & CSRF MANAGEMENT (PHASE 6.3.2 STAGE 6.1)
// ============================================================================
(function (global) {
  class ZiglagApiClient {
    constructor() {
      this._csrfToken = null;
      this._csrfPromise = null;
      this._inFlightLocks = new Set();
      this.baseUrl = ''; // relative path for same-origin
    }

    /**
     * Set or cache a known CSRF token (e.g. from /api/auth/me or /api/auth/login)
     */
    setCsrfToken(token) {
      if (typeof token === 'string' && token.trim()) {
        this._csrfToken = token.trim();
      }
    }

    /**
     * Retrieve the currently cached CSRF token, if any
     */
    getCachedCsrfToken() {
      return this._csrfToken;
    }

    /**
     * Clear in-memory authenticated client state
     */
    clearAuthState() {
      this._csrfToken = null;
      this._csrfPromise = null;
    }

    /**
     * Check if a specific lock key is currently in-flight
     */
    isLocked(lockKey) {
      return this._inFlightLocks.has(lockKey);
    }

    /**
     * Helper to run an async operation with duplicate submission protection
     */
    async withLock(lockKey, asyncFn) {
      if (!lockKey) return await asyncFn();
      if (this._inFlightLocks.has(lockKey)) {
        const err = new Error(`Action "${lockKey}" is already in progress.`);
        err.code = 'REQUEST_IN_PROGRESS';
        err.lockKey = lockKey;
        throw err;
      }
      this._inFlightLocks.add(lockKey);
      try {
        return await asyncFn();
      } finally {
        this._inFlightLocks.delete(lockKey);
      }
    }

    /**
     * Retrieve or refresh CSRF token from server
     * Token sources:
     * 1. GET /api/auth/csrf-token (open endpoint)
     * 2. GET /api/auth/me (authenticated session)
     */
    async fetchCsrfToken(forceRefresh = false) {
      if (!forceRefresh && this._csrfToken) {
        return this._csrfToken;
      }

      // If a fetch is already in flight, reuse its promise
      if (this._csrfPromise) {
        return await this._csrfPromise;
      }

      this._csrfPromise = (async () => {
        try {
          // Attempt 1: Fetch from /api/auth/csrf-token
          const res = await fetch(`${this.baseUrl}/api/auth/csrf-token`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
          });
          if (res.ok) {
            const data = await res.json();
            if (data && data.success && data.csrf_token) {
              this._csrfToken = data.csrf_token;
              return this._csrfToken;
            }
          }

          // Fallback Attempt 2: /api/auth/me
          const meRes = await fetch(`${this.baseUrl}/api/auth/me`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
          });
          if (meRes.ok) {
            const meData = await meRes.json();
            if (meData && meData.csrf_token) {
              this._csrfToken = meData.csrf_token;
              return this._csrfToken;
            }
          }
        } catch (_) {
          // Non-blocking network failure
        } finally {
          this._csrfPromise = null;
        }
        return this._csrfToken;
      })();

      return await this._csrfPromise;
    }

    /**
     * Handle HTTP 401 Unauthorized responses
     */
    handleUnauthorized() {
      this.clearAuthState();
      if (typeof window !== 'undefined' && window.location) {
        const currentPath = window.location.pathname || '';
        // Avoid redirect loops when already on login page
        if (!currentPath.includes('/login.html') && !currentPath.includes('/login')) {
          const next = encodeURIComponent(currentPath + (window.location.search || ''));
          window.location.href = `/login.html?next=${next}`;
        }
      }
    }

    /**
     * Core reusable request method
     *
     * @param {string} endpoint - API path (e.g. '/api/student/dashboard-summary')
     * @param {string} [method='GET'] - HTTP method ('GET', 'POST', 'PUT', 'DELETE', etc.)
     * @param {object|string|null} [payload=null] - Request body
     * @param {object} [options={}] - Additional options (lockKey, button, headers, _isRetry)
     * @returns {Promise<any>} Parsed response data
     */
    async request(endpoint, method = 'GET', payload = null, options = {}) {
      const normalizedMethod = (method || 'GET').toUpperCase();
      const lockKey = options.lockKey;
      const guardButton = options.button || options.guardButton;

      // Duplicate request prevention via lockKey
      if (lockKey) {
        if (this._inFlightLocks.has(lockKey)) {
          const err = new Error(`Request with lockKey "${lockKey}" is already in progress.`);
          err.code = 'REQUEST_IN_PROGRESS';
          err.lockKey = lockKey;
          throw err;
        }
        this._inFlightLocks.add(lockKey);
      }

      // Duplicate request prevention via button disablement
      if (guardButton) {
        if (guardButton.disabled) {
          const err = new Error('Action button is currently disabled.');
          err.code = 'BUTTON_DISABLED';
          throw err;
        }
        guardButton.disabled = true;
      }

      try {
        return await this._executeRequest(endpoint, normalizedMethod, payload, options);
      } finally {
        if (lockKey) {
          this._inFlightLocks.delete(lockKey);
        }
        if (guardButton) {
          guardButton.disabled = false;
        }
      }
    }

    async _executeRequest(endpoint, method, payload, options) {
      const isMutating = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);
      const headers = Object.assign({}, options.headers || {});

      // For mutating requests, attach CSRF token and Content-Type
      if (isMutating) {
        let token = this._csrfToken;
        if (!token) {
          token = await this.fetchCsrfToken();
        }
        if (token) {
          headers['X-CSRF-Token'] = token;
        }

        if (payload !== null && payload !== undefined && !(typeof FormData !== 'undefined' && payload instanceof FormData)) {
          if (!headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
          }
        }
      }

      const fetchOpts = {
        method: method,
        headers: headers
      };

      if (payload !== null && payload !== undefined && method !== 'GET' && method !== 'HEAD') {
        if (typeof payload === 'string' || (typeof FormData !== 'undefined' && payload instanceof FormData)) {
          fetchOpts.body = payload;
        } else {
          fetchOpts.body = JSON.stringify(payload);
        }
      }

      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

      let response;
      try {
        response = await fetch(url, fetchOpts);
      } catch (networkErr) {
        const err = new Error(`Network failure during ${method} ${endpoint}: ${networkErr.message}`);
        err.isNetworkError = true;
        err.originalError = networkErr;
        throw err;
      }

      // 1. Handle HTTP 401 Authentication Expiry
      if (response.status === 401) {
        this.handleUnauthorized();
        const errData = await this._parseResponseData(response);
        const err = new Error(errData && errData.message ? errData.message : 'Authentication required. Please sign in.');
        err.status = 401;
        err.code = (errData && errData.code) || 'UNAUTHORIZED';
        err.data = errData;
        throw err;
      }

      // 2. Handle HTTP 400 with CSRF_FAILED (Single Retry Logic)
      if (response.status === 400 && isMutating && !options._isRetry) {
        const clonedRes = response.clone();
        const errData = await this._parseResponseData(clonedRes);
        if (errData && errData.code === 'CSRF_FAILED') {
          // Force refresh CSRF token once
          const newToken = await this.fetchCsrfToken(true);
          if (newToken) {
            // Retry original request exactly once
            const retryOptions = Object.assign({}, options, { _isRetry: true });
            return await this._executeRequest(endpoint, method, payload, retryOptions);
          }
        }
      }

      // 3. Handle Other Error Responses
      if (!response.ok) {
        const errData = await this._parseResponseData(response);
        const msg = (errData && typeof errData === 'object' && errData.message)
          ? errData.message
          : (typeof errData === 'string' && errData)
            ? errData
            : `API request failed with HTTP ${response.status}`;
        const err = new Error(msg);
        err.status = response.status;
        err.code = (errData && typeof errData === 'object' && errData.code) || null;
        err.data = errData;
        throw err;
      }

      // 4. Handle Success Response
      return await this._parseResponseData(response);
    }

    async _parseResponseData(response) {
      const contentType = (response.headers && response.headers.get && response.headers.get('content-type')) || '';
      if (contentType.includes('application/json')) {
        try {
          return await response.json();
        } catch (_) {
          return null;
        }
      }
      try {
        const text = await response.text();
        try {
          return JSON.parse(text);
        } catch (_) {
          return text;
        }
      } catch (_) {
        return null;
      }
    }

    // Convenience shorthands
    get(endpoint, options = {}) {
      return this.request(endpoint, 'GET', null, options);
    }

    post(endpoint, payload = null, options = {}) {
      return this.request(endpoint, 'POST', payload, options);
    }

    put(endpoint, payload = null, options = {}) {
      return this.request(endpoint, 'PUT', payload, options);
    }

    delete(endpoint, payload = null, options = {}) {
      return this.request(endpoint, 'DELETE', payload, options);
    }
  }

  const apiInstance = new ZiglagApiClient();
  global.ZiglagAPI = apiInstance;
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));

// ============================================================================
// PHASE 6.4.3: REAL-TIME STUDY TIME TRACKER CLIENT
// ============================================================================
(function (global) {
  // Pure JS SHA-256 for deterministic payload hashing across all runtime contexts
  function _computeSha256(ascii) {
    function rightRotate(value, amount) {
      return (value >>> amount) | (value << (32 - amount));
    }
    const mathPow = Math.pow;
    const maxWord = mathPow(2, 32);
    let i, j;
    let result = '';
    const words = [];
    const asciiBitLength = ascii.length * 8;
    const hash = _computeSha256.h = _computeSha256.h || [];
    const k = _computeSha256.k = _computeSha256.k || [];
    let primeCounter = k.length;
    const isComposite = {};
    for (let candidate = 2; primeCounter < 64; candidate++) {
      if (!isComposite[candidate]) {
        for (i = 0; i < 313; i += candidate) {
          isComposite[i] = candidate;
        }
        hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
        k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
      }
    }
    ascii += '\x80';
    while ((ascii.length % 64) - 56) ascii += '\x00';
    for (i = 0; i < ascii.length; i++) {
      j = ascii.charCodeAt(i);
      if (j >> 8) return '';
      words[i >> 2] |= j << ((3 - i) % 4) * 8;
    }
    words[words.length] = (asciiBitLength / maxWord) | 0;
    words[words.length] = asciiBitLength;
    for (j = 0; j < words.length;) {
      const w = words.slice(j, j += 16);
      const oldHash = hash.slice(0, 8);
      for (i = 0; i < 64; i++) {
        const w15 = w[i - 15], w2 = w[i - 2];
        const a = hash[0], e = hash[4];
        const temp1 = hash[7]
          + (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25))
          + ((e & hash[5]) ^ ((~e) & hash[6]))
          + k[i]
          + (w[i] = (i < 16) ? w[i] : (
              w[i - 16]
              + (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3))
              + w[i - 7]
              + (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))
            ) | 0
          );
        const temp2 = (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22))
          + ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));
        hash[7] = hash[6];
        hash[6] = hash[5];
        hash[5] = hash[4];
        hash[4] = (hash[3] + temp1) | 0;
        hash[3] = hash[2];
        hash[2] = hash[1];
        hash[1] = hash[0];
        hash[0] = (temp1 + temp2) | 0;
      }
      for (i = 0; i < 8; i++) {
        hash[i] = (hash[i] + oldHash[i]) | 0;
      }
    }
    for (i = 0; i < 8; i++) {
      for (j = 3; j + 1; j--) {
        const b = (hash[i] >> (j * 8)) & 255;
        result += ((b < 16) ? '0' : '') + b.toString(16);
      }
    }
    return result;
  }

  async function sha256Hex(str) {
    if (typeof crypto !== 'undefined' && crypto.subtle && typeof TextEncoder !== 'undefined') {
      try {
        const msgUint8 = new TextEncoder().encode(str);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      } catch (_) {}
    }
    return _computeSha256(str);
  }

  class StudySessionTracker {
    constructor() {
      this.sessionToken = null;
      this.sessionId = null;
      this.courseId = null;
      this.lectureId = null;
      this.seq = 1;
      this.pendingPayloadHash = null;
      this.totalSeconds = 0;
      this.isDisplaced = false;
      this.isClosed = false;
      this.heartbeatTimer = null;
      this.intervalMs = 25000; // 25 seconds
      this.lastActivityTime = Date.now();
      this.idleThresholdMs = 30000; // 30 seconds
      this.isVideoPlaying = false;
      this.isSending = false;

      // Event callbacks
      this.onCredited = null;
      this.onDisplaced = null;
      this.onStatusChange = null;

      this._bindUserActivity();
      this._bindVisibility();
      this._bindUnload();
    }

    _bindUserActivity() {
      if (typeof window === 'undefined') return;
      const recordActive = () => {
        this.lastActivityTime = Date.now();
      };
      const events = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart', 'pointerdown'];
      let throttled = false;
      events.forEach(ev => {
        window.addEventListener(ev, () => {
          if (!throttled) {
            recordActive();
            throttled = true;
            setTimeout(() => { throttled = false; }, 1000);
          }
        }, { passive: true });
      });
    }

    _bindVisibility() {
      if (typeof document === 'undefined') return;
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
          this.lastActivityTime = Date.now();
        }
      });
    }

    _bindUnload() {
      if (typeof window === 'undefined') return;
      const handleExit = () => {
        this.closeSync('PAGE_UNLOAD');
      };
      window.addEventListener('pagehide', handleExit);
      window.addEventListener('beforeunload', handleExit);
    }

    setVideoPlaying(isPlaying) {
      this.isVideoPlaying = Boolean(isPlaying);
      if (this.isVideoPlaying) {
        this.lastActivityTime = Date.now();
      }
    }

    isUserActive() {
      if (typeof document !== 'undefined' && document.hidden) {
        return false;
      }
      if (this.isVideoPlaying) {
        return true;
      }
      return (Date.now() - this.lastActivityTime) < this.idleThresholdMs;
    }

    async start(courseId, lectureId) {
      if (!courseId || !lectureId) return null;

      // If already running for this exact lecture and not closed, reuse session
      if (this.sessionToken && this.courseId === courseId && this.lectureId === lectureId && !this.isClosed) {
        return { success: true, session_token: this.sessionToken, resumed: true };
      }

      // Close previous session if running
      if (this.sessionToken && !this.isClosed) {
        await this.close('SWITCH_LECTURE');
      }

      this._clearTimer();
      this.sessionToken = null;
      this.sessionId = null;
      this.courseId = courseId;
      this.lectureId = lectureId;
      this.seq = 1;
      this.pendingPayloadHash = null;
      this.totalSeconds = 0;
      this.isDisplaced = false;
      this.isClosed = false;
      this.lastActivityTime = Date.now();

      const api = global.ZiglagAPI;
      if (!api || typeof api.post !== 'function') {
        return null;
      }

      try {
        const res = await api.post('/api/student/study-session/start', {
          course_id: courseId,
          lecture_id: lectureId
        });

        if (res && res.success && res.session_token) {
          this.sessionToken = res.session_token;
          this.sessionId = res.session_id;
          this.isClosed = false;

          // Schedule periodic heartbeats
          this._scheduleNextHeartbeat();
          return res;
        }
      } catch (err) {
        console.warn('[StudyTracker] Failed to start study session:', err.message || err);
      }
      return null;
    }

    _scheduleNextHeartbeat() {
      this._clearTimer();
      if (this.isClosed) return;

      this.heartbeatTimer = setTimeout(async () => {
        if (!this.isClosed && this.sessionToken) {
          await this.sendHeartbeat('heartbeat');
          this._scheduleNextHeartbeat();
        }
      }, this.intervalMs);
    }

    _clearTimer() {
      if (this.heartbeatTimer) {
        clearTimeout(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }
    }

    async sendHeartbeat(eventType = 'heartbeat') {
      if (!this.sessionToken || this.isClosed || this.isSending) return null;

      const api = global.ZiglagAPI;
      if (!api) return null;

      const activeState = (eventType === 'takeover') ? true : this.isUserActive();
      const currentSeq = this.seq;

      // Idempotent duplicate retry support: if we already computed a hash for this seq (due to retry), reuse it
      if (!this.pendingPayloadHash) {
        const rawPayload = `${this.sessionToken}:${currentSeq}:${activeState}:${eventType}`;
        this.pendingPayloadHash = await sha256Hex(rawPayload);
      }
      const hash = this.pendingPayloadHash;

      this.isSending = true;
      try {
        const res = await api.post('/api/student/study-session/heartbeat', {
          session_token: this.sessionToken,
          course_id: this.courseId,
          lecture_id: this.lectureId,
          seq: currentSeq,
          payload_hash: hash,
          is_active: activeState,
          event_type: eventType
        });

        if (res && res.success) {
          // Success: increment sequence number and clear pending hash
          this.seq = currentSeq + 1;
          this.pendingPayloadHash = null;

          if (typeof res.session_total_seconds === 'number') {
            this.totalSeconds = res.session_total_seconds;
          }

          if (res.status === 'displaced') {
            this.isDisplaced = true;
            if (typeof this.onDisplaced === 'function') {
              this.onDisplaced(res.message || 'Another study session is active in a different tab.');
            }
          } else if (res.status === 'lease_acquired' || res.status === 'active') {
            this.isDisplaced = false;
            if (typeof this.onCredited === 'function') {
              this.onCredited({
                status: res.status,
                creditedSeconds: res.credited_seconds || 0,
                totalSeconds: this.totalSeconds
              });
            }
          } else if (res.status === 'idle') {
            if (typeof this.onStatusChange === 'function') {
              this.onStatusChange({ status: 'idle', totalSeconds: this.totalSeconds });
            }
          }
          return res;
        } else if (res && res.status === 'closed') {
          this.isClosed = true;
          this._clearTimer();
        }
      } catch (err) {
        // Network failure: do NOT increment this.seq. Retain this.pendingPayloadHash for duplicate retry.
        console.warn('[StudyTracker] Heartbeat transmission network notice:', err.message || err);
      } finally {
        this.isSending = false;
      }
      return null;
    }

    async requestTakeover() {
      if (!this.sessionToken || this.isClosed) return null;
      // Clear pending retry hash so new takeover hash is computed
      this.pendingPayloadHash = null;
      return await this.sendHeartbeat('takeover');
    }

    async close(reason = 'USER_NAVIGATION') {
      this._clearTimer();
      const token = this.sessionToken;
      this.isClosed = true;
      this.sessionToken = null;

      if (!token) return;

      const api = global.ZiglagAPI;
      if (api && typeof api.post === 'function') {
        try {
          await api.post('/api/student/study-session/close', {
            session_token: token,
            close_reason: reason
          });
        } catch (err) {
          console.warn('[StudyTracker] Close session notice:', err.message || err);
        }
      }
    }

    closeSync(reason = 'PAGE_UNLOAD') {
      this._clearTimer();
      const token = this.sessionToken;
      this.isClosed = true;
      this.sessionToken = null;

      if (!token || typeof navigator === 'undefined') return;

      try {
        const payload = JSON.stringify({ session_token: token, close_reason: reason });
        if (typeof fetch === 'function') {
          // Modern browsers allow keepalive: true in beforeunload/pagehide
          fetch('/api/student/study-session/close', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload,
            keepalive: true
          }).catch(() => {});
        } else if (navigator.sendBeacon) {
          const blob = new Blob([payload], { type: 'application/json' });
          navigator.sendBeacon('/api/student/study-session/close', blob);
        }
      } catch (_) {}
    }
  }

  global.ZiglagStudyTracker = new StudySessionTracker();
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));

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
