
    // Study Room logic
    let activeCourse = null;
    let activeLectureIndex = 0;
    
    // Playback state variables
    let playbackInterval = null;
    let playbackCurrent = 0;
    let playbackLength = 765; // 12:45 in seconds
    let isPlaying = false;

    // Rich Lectures Data for playlist mapping
    const COURSE_LECTURES = {
      'wassce-gce-neco-prep': [
        // Number Bases
          { title: "L1: Introduction and Conversion to Base 10", length: "05:15", seconds: 850, group: "Number Bases", videoUrl: "https://youtu.be/GEQUHlVc8r0" },
          { title: "L2: Conversion from Base 10 to Other Bases", length: "02:46", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/wpDJwLx-eRw" },
          { title: "L3: Interconversions Between Bases", length: "02:03", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/S_V3UZb1xv4" },
          { title: "L4: Specific Base System and Direct Conversions", length: "02:18", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/_dfRw3wOpDU" },
          { title: "L5: Operations in Base 2", length: "07:06", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/bYrY_PAx4BA" },
          { title: "L6: Algebraic Equations in Number Bases", length: "04:26", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/9cZdSc4SW_Q" },
      ],
      'jamb-postjamb-prep': [
       // Number Bases
          { title: "L1: Introduction and Conversion to Base 10", length: "05:15", seconds: 850, group: "Number Bases", videoUrl: "https://youtu.be/GEQUHlVc8r0" },
          { title: "L2: Conversion from Base 10 to Other Bases", length: "02:46", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/wpDJwLx-eRw" },
          { title: "L3: Interconversions Between Bases", length: "02:03", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/S_V3UZb1xv4" },
          { title: "L4: Specific Base System and Direct Conversions", length: "02:18", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/_dfRw3wOpDU" },
          { title: "L5: Operations in Base 2", length: "07:06", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/bYrY_PAx4BA" },
          { title: "L6: Algebraic Equations in Number Bases", length: "04:26", seconds: 765, group: "Number Bases", videoUrl: "https://youtu.be/9cZdSc4SW_Q" },
      ],
      'other-exams-prep': [
        // IGCSE Mathematics (0580)
        { title: "L1: Algebraic Fractions Equations", length: "15:45", seconds: 945, group: "IGCSE Mathematics (0580)" },
        { title: "L2: Tree Diagrams & Probability", length: "13:10", seconds: 790, group: "IGCSE Mathematics (0580)" },
        // A-Level Pure Mathematics
        { title: "L3: Proof by Induction Theorems", length: "22:30", seconds: 1350, group: "A-Level Pure Mathematics" },
        { title: "L4: 3D Vector Geometry Dot Product", length: "24:15", seconds: 1455, group: "A-Level Pure Mathematics" }
      ],
      'undergrad-math-courses': [
        // Linear Algebra
        { title: "L1: Vector Spaces & Linear Independence", length: "23:45", seconds: 1425, group: "Linear Algebra" },
        { title: "L2: Eigenvalues & Diagonalization", length: "21:30", seconds: 1290, group: "Linear Algebra" },
        // Multivariable Calculus
        { title: "L3: Partial Derivatives & Gradient Vector", length: "20:15", seconds: 1215, group: "Multivariable Calculus" },
        { title: "L4: Double Integrals over regions", length: "22:50", seconds: 1370, group: "Multivariable Calculus" }
      ],
      'extras-general-videos': [
        // Showcase & Walkthroughs
        { title: "L1: Ziglag Portal Features Walkthrough", length: "11:50", seconds: 710, group: "Showcase & Walkthroughs", videoUrl: "render 4k.mp4" },
        { title: "L2: 4K Render Animation Showcase", length: "09:40", seconds: 580, group: "Showcase & Walkthroughs" },
        // Math History & Curiosities
        { title: "L3: Euler's Identity - Mathematical Beauty", length: "16:20", seconds: 980, group: "Math History & Curiosities" },
        { title: "L4: The Fibonacci Sequence in Nature", length: "13:40", seconds: 820, group: "Math History & Curiosities" },
        //New Videos From YouTube Channel
        { title: "L5: An Advanced Limit problem involving Factorial", length: "02:36", seconds: 156, group: "YouTube Channel", videoUrl: "https://youtu.be/83q5G1J01Mo?si=tDCvBC_Subd0Omkl" }
      ],
      'wassce-gce-neco-physics': [
        // Mechanics
        { title: "L1: Kinematics & Projectiles", length: "15:20", seconds: 920, group: "Mechanics" },
        { title: "L2: Circular Motion Mechanics", length: "14:10", seconds: 850, group: "Mechanics" },
        // Thermal & Waves
        { title: "L3: Thermal Expansion Equations", length: "13:30", seconds: 810, group: "Thermal & Waves" },
        { title: "L4: Wave Propagation & Sound", length: "12:50", seconds: 770, group: "Thermal & Waves" },
        // Electricity & Magnetism
        { title: "L5: Current Electricity & Ohms Law", length: "16:45", seconds: 1005, group: "Electricity & Magnetism" },
        { title: "L6: Electrostatics Induction", length: "18:30", seconds: 1110, group: "Electricity & Magnetism" }
      ],
      'jamb-postjamb-physics': [
        // Mechanics & Heat
        { title: "L1: Motion & Forces UTME Hacks", length: "14:10", seconds: 850, group: "Mechanics & Heat" },
        { title: "L2: Gas Laws & Thermal expansion", length: "13:20", seconds: 800, group: "Mechanics & Heat" },
        // Electricity & Light
        { title: "L3: Refraction & Lens Equations", length: "12:45", seconds: 765, group: "Electricity & Light" },
        { title: "L4: Electrostatics & Potential UTME", length: "15:10", seconds: 910, group: "Electricity & Light" },
        // Modern Physics
        { title: "L5: Half-Life Decay Calculations", length: "11:55", seconds: 715, group: "Modern Physics" },
        { title: "L6: Photoelectric Effects & Spectra", length: "13:40", seconds: 820, group: "Modern Physics" }
      ],
      'other-exams-physics': [
        // IGCSE Physics
        { title: "L1: Density, Force & Elastic Hooke", length: "14:10", seconds: 850, group: "IGCSE Physics" },
        { title: "L2: Thermal Transfer & Specific Heat", length: "12:45", seconds: 765, group: "IGCSE Physics" },
        // A-Level Physics
        { title: "L3: Gravitational & Coulomb Field Math", length: "22:15", seconds: 1335, group: "A-Level Physics" },
        { title: "L4: Nuclear Structure & Half-Life Decay", length: "24:30", seconds: 1470, group: "A-Level Physics" }
      ]
    };

    // Course interactive Practice Quizzes
    const COURSE_QUIZZES = {
      'wassce-gce-neco-prep': {
        q: "If x is a base-10 integer, solve for x in the modular congruence equation:",
        formula: `<span class="math-symbol">3x</span> <span class="math-op">≡</span> <span style="font-size:1.1rem;">4</span> <span class="math-symbol">(mod 5)</span>`,
        options: [
          "x = 1",
          "x = 3",
          "x = 2",
          "x = 4"
        ],
        answer: 1,
        explain: "Testing options: 3(3) = 9. When 9 is divided by 5, the remainder is 4. Thus, 9 ≡ 4 (mod 5), making x = 3 the correct solution."
      },
      'jamb-postjamb-prep': {
        q: "Evaluate the logarithmic equation for the real variable y:",
        formula: `<span class="math-symbol">log</span><sub style="margin-left:-28px; font-size:0.75rem; vertical-align:sub; position:relative; top:8px;">2</sub>(<span class="math-symbol">y</span>² <span class="math-op">-</span> <span style="font-size:1.1rem;">1</span>) <span class="math-op">=</span> <span style="font-size:1.1rem;">3</span>`,
        options: [
          "y = ±3",
          "y = ±2",
          "y = ±4",
          "y = ±9"
        ],
        answer: 0,
        explain: "Converting the logarithm to exponential form yields: y² - 1 = 2³ = 8. So, y² = 9, which means y = ±3."
      },
      'other-exams-prep': {
        q: "Solve the A-Level Pure Mathematics integral of the given algebraic fractional expansion:",
        formula: `<span class="math-integral">∫</span> <div class="math-frac" style="font-size:0.8rem;"><span class="math-num">1</span><span class="math-den"><span class="math-symbol">x</span>² <span class="math-op">-</span> <span style="font-size:0.85rem;">1</span></span></div> <span class="math-symbol">dx</span>`,
        options: [
          "0.5 ln |(x-1)/(x+1)| + C",
          "ln |x² - 1| + C",
          "arctan(x) + C",
          "0.5 ln |(x+1)/(x-1)| + C"
        ],
        answer: 0,
        explain: "Applying partial fraction decomposition yields 1/(x²-1) = 0.5[1/(x-1) - 1/(x+1)]. Integrating both terms gives 0.5 [ln|x-1| - ln|x+1|] + C = 0.5 ln|(x-1)/(x+1)| + C."
      },
      'undergrad-math-courses': {
        q: "Let V be a vector space, and S = {v₁, v₂} be linear independent. Which of the following defines a spanning set of a subspace?",
        formula: `<span class="math-symbol">U</span> <span class="math-op">=</span> <span class="math-symbol">span</span>({<span class="math-symbol">v₁</span> <span class="math-op">+</span> <span class="math-symbol">v₂</span>, <span class="math-symbol">v₁</span> <span class="math-op">-</span> <span class="math-symbol">v₂</span>})`,
        options: [
          "U has a dimension of 1 because adding elements reduces independent rank.",
          "U has a dimension of 2 because vector sum/difference are linearly independent.",
          "U is not a subspace because span boundaries are open.",
          "U spans the zero vector only."
        ],
        answer: 1,
        explain: "Adding and subtracting two independent vectors v₁ and v₂ produces a linear system whose rank remains exactly 2. Thus, the span retains dimension = 2."
      },
      'wassce-gce-neco-physics': {
        q: "State the mathematical formula representing Ohm's Law in electric circuits:",
        formula: `<span class="math-symbol">V</span> <span class="math-op">=</span> <span class="math-symbol">I</span> <span class="math-symbol">R</span>`,
        options: [
          "V = I / R",
          "V = I² R",
          "V = I R",
          "V = R / I"
        ],
        answer: 2,
        explain: "Ohm's Law states that the voltage V across a conductor is directly proportional to the current I flowing through it, with resistance R as the constant of proportionality."
      },
      'jamb-postjamb-physics': {
        q: "Solve for the work done when a force of 10 N moves a body by 5 meters in the direction of the force:",
        formula: `<span class="math-symbol">Work</span> <span class="math-op">=</span> <span class="math-symbol">F</span> <span class="math-op">×</span> <span class="math-symbol">d</span>`,
        options: [
          "15 Joules",
          "50 Joules",
          "2 Joules",
          "25 Joules"
        ],
        answer: 1,
        explain: "Work is calculated as Force multiplied by displacement. Work = 10 N × 5 m = 50 Joules."
      },
    };

    // Alias mappings for all course ID variations
    COURSE_LECTURES['utme-postutme-prep'] = COURSE_LECTURES['jamb-postjamb-prep'];
    COURSE_LECTURES['utme-postutme-physics'] = COURSE_LECTURES['jamb-postjamb-physics'];
    COURSE_LECTURES['jamb-prep'] = COURSE_LECTURES['jamb-postjamb-prep'];
    COURSE_LECTURES['post-jamb-prep'] = COURSE_LECTURES['jamb-postjamb-prep'];
    COURSE_LECTURES['wassce-gce-prep'] = COURSE_LECTURES['wassce-gce-neco-prep'];
    COURSE_LECTURES['neco-prep'] = COURSE_LECTURES['wassce-gce-neco-prep'];

    COURSE_QUIZZES['utme-postutme-prep'] = COURSE_QUIZZES['jamb-postjamb-prep'];
    COURSE_QUIZZES['utme-postutme-physics'] = COURSE_QUIZZES['jamb-postjamb-physics'];
    COURSE_QUIZZES['jamb-prep'] = COURSE_QUIZZES['jamb-postjamb-prep'];
    COURSE_QUIZZES['post-jamb-prep'] = COURSE_QUIZZES['jamb-postjamb-prep'];
    COURSE_QUIZZES['wassce-gce-prep'] = COURSE_QUIZZES['wassce-gce-neco-prep'];
    COURSE_QUIZZES['neco-prep'] = COURSE_QUIZZES['wassce-gce-neco-prep'];

    document.addEventListener("DOMContentLoaded", () => {
      // Find course parameters
      const params = new URLSearchParams(window.location.search);
      const cid = params.get("id") || "wassce-gce-neco-prep";
      
      activeCourse = MATH_DATABASE.courses.find(c => c.id === cid) || MATH_DATABASE.courses[0];
      
      // Inject course content details
      document.getElementById("overview-course-title").innerText = activeCourse.title;
      document.getElementById("overview-course-desc").innerText = activeCourse.shortDesc;
      
      const modulesList = document.getElementById("overview-modules-list");
      modulesList.innerHTML = activeCourse.syllabus.map(m => `
        <li style="display:flex; align-items:center; gap:0.75rem;">
          <span style="background:rgba(99,102,241,0.1); width:28px; height:28px; border-radius:50%; display:flex; justify-content:center; align-items:center; color:var(--primary-color); font-weight:bold; font-size:0.85rem;">✓</span>
          <span style="color:var(--text-main); font-weight:500;">${m}</span>
        </li>
      `).join('');

      // Listen to real video ended events to auto-complete the lesson
      const videoPlayer = document.getElementById("actual-video-player");
      videoPlayer.addEventListener("ended", () => {
        const lectures = COURSE_LECTURES[activeCourse.id] || COURSE_LECTURES['wassce-gce-neco-prep'];
        if (lectures[activeLectureIndex]) {
          AppState.toggleLessonComplete(activeCourse.id, `lec-${activeLectureIndex}`);
          renderPlaylist();
          updateProgressUI();
          alert("Lecture completed! Progress saved.");
        }
      });

      renderPlaylist();
      renderQuiz();
      updateProgressUI();
    });

    function renderPlaylist() {
      const list = document.getElementById("lecture-playlist-items");
      list.innerHTML = "";
      
      const lectures = COURSE_LECTURES[activeCourse.id] || COURSE_LECTURES['wassce-gce-neco-prep'];
      
      // Sync playlist progress state with local storage
      const completedList = AppState.completedLessons[activeCourse.id] || [];

      let lastGroup = null;

      lectures.forEach((l, index) => {
        // Group heading separator
        if (l.group && l.group !== lastGroup) {
          const header = document.createElement("li");
          header.className = "playlist-group-header";
          header.style.padding = "0.6rem 0.75rem";
          header.style.color = "var(--secondary-color)";
          header.style.fontWeight = "600";
          header.style.fontSize = "0.78rem";
          header.style.letterSpacing = "0.03em";
          header.style.textTransform = "uppercase";
          header.style.background = "rgba(255, 255, 255, 0.02)";
          header.style.borderLeft = "3px solid var(--secondary-color)";
          header.style.marginTop = "0.75rem";
          header.style.marginBottom = "0.25rem";
          header.style.listStyle = "none";
          header.style.borderRadius = "var(--radius-sm)";
          header.innerText = l.group;
          list.appendChild(header);
          lastGroup = l.group;
        }

        const item = document.createElement("li");
        const isCompleted = completedList.includes(`lec-${index}`);
        const isActive = activeLectureIndex === index;
        
        item.className = `playlist-item ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`;
        item.onclick = () => selectLecture(index);
        
        item.innerHTML = `
          <div class="playlist-status"></div>
          <div style="flex:1;">
            <p style="font-weight: 500; font-size: 0.9rem; color: var(--text-main); margin:0;">${l.title}</p>
            <span style="font-size:0.75rem; color:var(--text-muted);">Duration: ${l.length} mins</span>
          </div>
          <button class="btn btn-secondary btn-sm" style="padding:0.2rem 0.4rem; border:none; background:transparent; font-size: 0.8rem;" onclick="toggleComplete(event, ${index})">
            ${isCompleted ? '↩ Reset' : '✓ Done'}
          </button>
        `;
        
        list.appendChild(item);
      });
    }

    function selectLecture(index) {
      activeLectureIndex = index;
      
      // Stop ongoing mock video playback
      stopMockPlayback();
      
      // Pause and hide actual HTML5 video and YouTube iframe players
      const videoPlayer = document.getElementById("actual-video-player");
      videoPlayer.pause();
      videoPlayer.style.display = "none";
      
      const iframePlayer = document.getElementById("iframe-video-player");
      iframePlayer.src = "";
      iframePlayer.style.display = "none";
      
      // Show controls bar by default
      document.getElementById("mock-controls-bar").style.display = "flex";
      
      const lectures = COURSE_LECTURES[activeCourse.id] || COURSE_LECTURES['grade-4-12-math'];
      const lecture = lectures[index];
      
      playbackLength = lecture.seconds;
      playbackCurrent = 0;
      
      document.getElementById("video-status").innerText = "Start: " + lecture.title;
      document.getElementById("video-blackboard-title").innerText = lecture.title;
      document.getElementById("mini-time-display").innerText = "00:00 / " + lecture.length;
      document.getElementById("video-timer").innerText = "Progress: 00:00 / " + lecture.length;
      document.getElementById("video-progress-bar").style.width = "0%";

      // Reset Active Class
      const items = document.querySelectorAll(".playlist-item");
      items.forEach((item, idx) => {
        if (idx === index) {
          item.classList.add("active");
        } else {
          item.classList.remove("active");
        }
      });

      // Handle real video or YouTube embed playback if videoUrl is supplied
      if (lecture.videoUrl) {
        document.getElementById("video-overlay").style.display = "none";
        document.getElementById("video-blackboard").style.display = "none";
        document.getElementById("mock-controls-bar").style.display = "none";
        
        let targetUrl = lecture.videoUrl;
        
        if (targetUrl.includes("youtube.com") || targetUrl.includes("youtu.be") || targetUrl.includes("drive.google.com")) {
          iframePlayer.style.display = "block";
          
          // Auto-convert standard YouTube watch links or Google Drive view links to embed preview format
          if (targetUrl.includes("watch?v=")) {
            const videoId = targetUrl.split("watch?v=")[1].split("&")[0];
            targetUrl = `https://www.youtube.com/embed/${videoId}`;
          } else if (targetUrl.includes("youtu.be/")) {
            const videoId = targetUrl.split("youtu.be/")[1].split("?")[0].split("&")[0];
            targetUrl = `https://www.youtube.com/embed/${videoId}`;
          } else if (targetUrl.includes("drive.google.com") && targetUrl.includes("/view")) {
            targetUrl = targetUrl.replace(/\/view.*/, "/preview");
          }

          if (lecture.videoUrl.includes("drive.google.com")) {
            const directDriveUrl = lecture.videoUrl.replace("/preview", "/view");
            const noticeBox = document.getElementById("drive-mobile-notice");
            const noticeBtn = document.getElementById("drive-direct-link");
            if (noticeBox && noticeBtn) {
              noticeBtn.href = directDriveUrl;
              noticeBox.style.display = "block";
            }
          } else {
            const noticeBox = document.getElementById("drive-mobile-notice");
            if (noticeBox) noticeBox.style.display = "none";
          }
          
          iframePlayer.src = targetUrl;
        } else {
          const noticeBox = document.getElementById("drive-mobile-notice");
          if (noticeBox) noticeBox.style.display = "none";
          
          videoPlayer.style.display = "block";
          videoPlayer.src = targetUrl;
          videoPlayer.load();
          videoPlayer.play().catch(e => console.log("Playback failed or was blocked by browser autoplay rules: ", e));
        }
      } else {
        const noticeBox = document.getElementById("drive-mobile-notice");
        if (noticeBox) noticeBox.style.display = "none";
        
        // Restore standard mock overlay view
        document.getElementById("video-overlay").style.display = "flex";
      }
    }

    function toggleComplete(event, index) {
      event.stopPropagation();
      const didComplete = AppState.toggleLessonComplete(activeCourse.id, `lec-${index}`);
      
      renderPlaylist();
      updateProgressUI();
    }

    function updateProgressUI() {
      const lectures = COURSE_LECTURES[activeCourse.id] || COURSE_LECTURES['grade-4-12-math'];
      const total = lectures.length;
      const done = AppState.getCompletedCount(activeCourse.id);
      const percent = Math.round((done / total) * 100);

      document.getElementById("study-progress-text").innerText = `${done} / ${total} Lectures (${percent}%)`;
      document.getElementById("study-progress-bar").style.width = `${percent}%`;
    }

    // Video playback mocks
    function startMockPlayback() {
      document.getElementById("video-overlay").style.display = "none";
      document.getElementById("video-blackboard").style.display = "flex";
      
      isPlaying = true;
      playbackInterval = setInterval(() => {
        if (playbackCurrent < playbackLength) {
          playbackCurrent++;
          updatePlaybackUI();
        } else {
          stopMockPlayback();
          // Automatically mark lecture as complete!
          AppState.toggleLessonComplete(activeCourse.id, `lec-${activeLectureIndex}`);
          renderPlaylist();
          updateProgressUI();
          alert("Lecture completed! Progress saved.");
        }
      }, 1000);
    }

    function stopMockPlayback() {
      clearInterval(playbackInterval);
      playbackInterval = null;
      isPlaying = false;
      document.getElementById("video-overlay").style.display = "flex";
      document.getElementById("video-blackboard").style.display = "none";
      document.getElementById("video-status").innerText = "Resume Lecture";
    }

    function togglePlayPause() {
      if (isPlaying) {
        stopMockPlayback();
      } else {
        startMockPlayback();
      }
    }

    function formatTime(sec) {
      const mins = Math.floor(sec / 60);
      const secs = sec % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function updatePlaybackUI() {
      const progressPercent = (playbackCurrent / playbackLength) * 100;
      document.getElementById("video-progress-bar").style.width = `${progressPercent}%`;
      
      const timeStr = `${formatTime(playbackCurrent)} / ${formatTime(playbackLength)}`;
      document.getElementById("mini-time-display").innerText = timeStr;
      document.getElementById("video-timer").innerText = "Progress: " + timeStr;
    }

    function seekVideo(event) {
      if (!isPlaying) return;
      const progressContainer = event.currentTarget;
      const rect = progressContainer.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const width = rect.width;
      
      const clickPercent = clickX / width;
      playbackCurrent = Math.floor(clickPercent * playbackLength);
      updatePlaybackUI();
    }

    // Tabs Manager
    function switchStudyTab(tabName) {
      const tabs = ['overview', 'scratchpad', 'quiz'];
      tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const content = document.getElementById(`content-${t}`);
        if (t === tabName) {
          btn.classList.add('active');
          content.style.display = 'block';
        } else {
          btn.classList.remove('active');
          content.style.display = 'none';
        }
      });
    }

    // Scratchpad manager
    function insertMathSymbol(symbol) {
      const textarea = document.getElementById("math-notes");
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = textarea.value;
      
      textarea.value = text.substring(0, start) + symbol + text.substring(end);
      textarea.focus();
      textarea.selectionStart = textarea.selectionEnd = start + symbol.length;
    }

    function clearScratchpad() {
      if (confirm("Are you sure you want to clear your scratchpad notes?")) {
        document.getElementById("math-notes").value = "";
      }
    }

    // Quiz Manager
    function renderQuiz() {
      const quiz = COURSE_QUIZZES[activeCourse.id] || COURSE_QUIZZES['linear-algebra'];
      
      document.getElementById("quiz-question-title").innerText = quiz.q;
      document.getElementById("quiz-math-container").innerHTML = quiz.formula;
      
      const optContainer = document.getElementById("quiz-answers-container");
      optContainer.innerHTML = "";
      
      quiz.options.forEach((opt, index) => {
        const btn = document.createElement("button");
        btn.className = "btn btn-secondary";
        btn.style.textAlign = "left";
        btn.style.justifyContent = "flex-start";
        btn.innerHTML = `<span style="background:rgba(255,255,255,0.06); width:24px; height:24px; border-radius:50%; display:inline-flex; justify-content:center; align-items:center; margin-right: 0.75rem; font-weight:bold; font-size:0.8rem;">${String.fromCharCode(65 + index)}</span> ${opt}`;
        btn.onclick = () => submitQuizAnswer(index, quiz.answer, quiz.explain);
        
        optContainer.appendChild(btn);
      });

      // Clear previous feedbacks
      const fbBox = document.getElementById("quiz-feedback-box");
      fbBox.style.display = "none";
    }

    function submitQuizAnswer(selectedIndex, correctIndex, explainText) {
      const fbBox = document.getElementById("quiz-feedback-box");
      const fbText = document.getElementById("quiz-feedback-text");
      
      fbBox.style.display = "block";
      
      if (selectedIndex === correctIndex) {
        fbBox.style.borderColor = "var(--accent-color)";
        fbBox.style.background = "rgba(6, 182, 212, 0.08)";
        fbText.innerHTML = `<span style="color:var(--accent-color); font-weight:700;">⭐ Correct!</span> ${explainText}`;
      } else {
        fbBox.style.borderColor = "rgba(239, 68, 68, 0.3)";
        fbBox.style.background = "rgba(239, 68, 68, 0.05)";
        fbText.innerHTML = `<span style="color:#f87171; font-weight:700;">❌ Incorrect.</span> Try reviewing the lecture blackboard concepts! Correct answer was Option ${String.fromCharCode(65 + correctIndex)}.`;
      }
    }
  