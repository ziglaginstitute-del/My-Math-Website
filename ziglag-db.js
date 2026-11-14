/**
 * Ziglag Institute Math Portal - Universal Database Layer
 * Completely independent of Supabase.
 * Connects directly to backend database (Local SQLite or Cloud PostgreSQL/Neon)
 * with graceful offline local-storage fallback.
 */

(function (window) {
  'use strict';

  // API helper
  function getApiBaseUrl() {
    if (typeof window !== 'undefined' && window.location) {
      if (window.location.protocol === 'file:' || !window.location.host) {
        return 'http://127.0.0.1:5000';
      }
    }
    return '';
  }

  async function apiRequest(endpoint, method = 'GET', body = null) {
    const baseUrl = getApiBaseUrl();
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;
    const opts = {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      opts.body = JSON.stringify(body);
    }
    const response = await fetch(fullUrl, opts);
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`API error (${response.status}): ${err}`);
    }
    return await response.json();
  }

  const ZiglagDB = {
    utils: {
      parseYouTubeId: function (url) {
        if (!url) return null;
        const regExp = /(?:youtube\.com\/(?:watch\?.*v=|embed\/|shorts\/|live\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regExp);
        return (match && match[1]) ? match[1] : null;
      },
      normalizeVideoUrl: function (url) {
        if (!url) return "";
        const trimmed = url.trim();
        const ytId = this.parseYouTubeId(trimmed);
        if (ytId) {
          return `https://www.youtube.com/embed/${ytId}`;
        }
        if (trimmed.includes("drive.google.com") && trimmed.includes("/view")) {
          return trimmed.replace(/\/view.*/, "/preview");
        }
        return trimmed;
      }
    },

    config: {
      getUrl: function () {
        return localStorage.getItem('ZIGLAG_DB_URL') || '/api';
      },
      getKey: function () {
        return localStorage.getItem('ZIGLAG_DB_KEY') || 'internal';
      },
      setCredentials: function (url) {
        if (url) localStorage.setItem('ZIGLAG_DB_URL', url.trim());
      },
      resetCredentials: function () {
        localStorage.removeItem('ZIGLAG_DB_URL');
      },
      testConnection: async function () {
        try {
          const res = await apiRequest('/api/db-status');
          if (res.success) {
            return {
              success: true,
              provider: res.provider,
              message: `Connected to ${res.provider}! (${res.candidates_count} candidates, ${res.questions_count} questions)`,
              count: res.candidates_count
            };
          }
          return { success: false, message: res.error || 'Connection error' };
        } catch (e) {
          // Offline fallback
          return { success: false, message: 'Offline mode active (using local browser storage)' };
        }
      }
    },

    candidates: {
      // Lookup candidate by registration number (username)
      verify: async function (regNumber) {
        if (!regNumber) return null;
        const cleanReg = regNumber.trim();
        try {
          const res = await apiRequest('/api/candidates/verify', 'POST', { reg_number: cleanReg });
          if (res.success && res.candidate) return res.candidate;
        } catch (err) {
          console.warn('[ZiglagDB] API verify notice, checking local store:', err);
        }

        // Local storage fallback for offline mocks
        const localCandidates = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_CANDIDATES') || '[]');
        return localCandidates.find(c => 
          c.username?.toLowerCase() === cleanReg.toLowerCase() || 
          c.reg_number?.toLowerCase() === cleanReg.toLowerCase() ||
          c.id?.toLowerCase() === cleanReg.toLowerCase() ||
          c.email?.toLowerCase() === cleanReg.toLowerCase()
        ) || null;
      },

      list: async function () {
        try {
          return await apiRequest('/api/candidates');
        } catch (e) {
          console.warn('[ZiglagDB] Falling back to local candidates:', e);
          return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_CANDIDATES') || '[]');
        }
      },

      
      bulkRegister: async function (candidatesList) {
        try {
          const res = await apiRequest('/api/candidates/bulk', 'POST', candidatesList);
          if (res.success) return res.candidates;
        } catch (e) {
          console.warn('[ZiglagDB] Bulk candidate register notice:', e);
        }
        const list = await this.list();
        const merged = [...candidatesList, ...list];
        localStorage.setItem('ZIGLAG_LOCAL_CANDIDATES', JSON.stringify(merged));
        return candidatesList;
      },

      delete: async function (candidateId) {
        try {
          await apiRequest(`/api/candidates/${encodeURIComponent(candidateId)}`, 'DELETE');
        } catch (e) {}
        let list = await this.list();
        list = list.filter(c => c.id !== candidateId && c.username !== candidateId);
        localStorage.setItem('ZIGLAG_LOCAL_CANDIDATES', JSON.stringify(list));
        return true;
      },

      reset: async function (candidateId) {
        try {
          const res = await apiRequest(`/api/candidates/${encodeURIComponent(candidateId)}/reset`, 'POST');
          return res;
        } catch (e) {
          console.warn('[ZiglagDB] Reset exam notice:', e);
          return { success: true };
        }
      },

      register: async function (candidateData) {
        try {
          const res = await apiRequest('/api/candidates/register', 'POST', candidateData);
          if (res.success && res.candidate) return res.candidate;
        } catch (e) {
          console.warn('[ZiglagDB] Server register failed, storing locally:', e);
        }

        // Offline local fallback
        const payload = {
          id: candidateData.id || 'cand_' + Date.now(),
          full_name: candidateData.full_name || candidateData.fullName,
          username: (candidateData.username || candidateData.reg_number || 'ZIG/' + Date.now().toString().slice(-6)).toUpperCase(),
          password: candidateData.password || '123456',
          email: candidateData.email || '',
          phone: candidateData.phone || '',
          category: candidateData.category || 'Science',
          exam_type: candidateData.exam_type || 'JAMB UTME',
          registered_subjects: candidateData.registered_subjects || ["english", "mathematics", "physics", "chemistry"],
          center: candidateData.center || 'Ziglag CBT Center Lagos',
          seat_number: candidateData.seat_number || 'Seat 01',
          status: 'Active',
          created_at: new Date().toISOString()
        };
        const list = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_CANDIDATES') || '[]');
        list.unshift(payload);
        localStorage.setItem('ZIGLAG_LOCAL_CANDIDATES', JSON.stringify(list));
        return payload;
      }
    },

    exams: {
      listActive: async function () {
        try {
          return await apiRequest('/api/exams');
        } catch (e) {
          return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_EXAMS') || '[]');
        }
      },

      create: async function (examData) {
        try {
          const res = await apiRequest('/api/exams', 'POST', examData);
          if (res.success && res.exam) return res.exam;
        } catch (e) {
          console.warn('[ZiglagDB] Server exam creation failed, storing locally:', e);
        }

        const payload = {
          id: 'mock_' + Date.now(),
          title: examData.title,
          access_code: (examData.access_code || 'MOCK-' + Math.random().toString(36).substring(2, 6)).toUpperCase(),
          exam_type: examData.exam_type || 'jamb',
          duration_minutes: parseInt(examData.duration_minutes || 120, 10),
          starts_at: examData.starts_at || new Date().toISOString(),
          ends_at: examData.ends_at || new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
          is_active: true
        };
        const list = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_EXAMS') || '[]');
        list.unshift(payload);
        localStorage.setItem('ZIGLAG_LOCAL_EXAMS', JSON.stringify(list));
        return payload;
      },

      
      delete: async function (examId) {
        try {
          await apiRequest(`/api/exams/${encodeURIComponent(examId)}`, 'DELETE');
        } catch (e) {}
        let list = await this.listActive();
        list = list.filter(ex => ex.id !== examId);
        localStorage.setItem('ZIGLAG_LOCAL_EXAMS', JSON.stringify(list));
        return true;
      },

      toggleActive: async function (examId, isActive) {
        try {
          return await apiRequest(`/api/exams/${encodeURIComponent(examId)}`, 'PUT', { is_active: isActive });
        } catch (e) {}
        return { success: true };
      },

      getReleaseStatus: async function () {
        try {
          const res = await apiRequest('/api/exams/release-status');
          return res.released;
        } catch (e) {
          return localStorage.getItem('ZIGLAG_RESULTS_RELEASED') !== 'false';
        }
      },

      setReleaseStatus: async function (released) {
        try {
          await apiRequest('/api/exams/release-status', 'POST', { released });
        } catch (e) {}
        localStorage.setItem('ZIGLAG_RESULTS_RELEASED', released ? 'true' : 'false');
        return released;
      },

      submitResult: async function (resultData) {
        try {
          const res = await apiRequest('/api/exams/submit', 'POST', resultData);
          if (res.success) return res.submission;
        } catch (e) {
          console.warn('[ZiglagDB] Online submit failed, caching locally:', e);
        }

        const payload = {
          id: 'sub_' + Date.now(),
          candidate_name: resultData.candidate_name || 'Anonymous',
          candidate_reg: resultData.candidate_reg || 'PRACTICE',
          exam_type: resultData.exam_type || 'JAMB UTME',
          score: resultData.score || 0,
          max_score: resultData.max_score || 400,
          percentage: resultData.percentage || 0,
          time_spent_seconds: resultData.time_spent_seconds || 0,
          created_at: new Date().toISOString()
        };
        const list = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_RESULTS') || '[]');
        list.unshift(payload);
        localStorage.setItem('ZIGLAG_LOCAL_RESULTS', JSON.stringify(list));
        return payload;
      },

      listHistory: async function () {
        try {
          return await apiRequest('/api/exams/history');
        } catch (e) {
          return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_RESULTS') || '[]');
        }
      }
    },

    questions: {
      list: async function (subject, limit = 50) {
        try {
          let url = `/api/questions?limit=${limit}`;
          if (subject) url += `&subject=${encodeURIComponent(subject.toLowerCase())}`;
          const list = await apiRequest(url);
          if (list && list.length > 0) return list;
        } catch (e) {
          console.warn('[ZiglagDB] Question query error, checking local bank:', e);
        }

        if (window.CBT_QUESTIONS_BANK && window.CBT_QUESTIONS_BANK[subject]) {
          return window.CBT_QUESTIONS_BANK[subject];
        }
        return [];
      },

      create: async function (q) {
        try {
          const res = await apiRequest('/api/questions', 'POST', q);
          if (res.success && res.question) return res.question;
        } catch (e) {
          console.warn('[ZiglagDB] Question insert failed, storing locally:', e);
        }

        const payload = {
          id: 'q_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
          subject: (q.subject || 'mathematics').lowerCase ? q.subject.toLowerCase() : 'mathematics',
          topic: q.topic || 'General',
          difficulty: q.difficulty || 'Intermediate',
          question_text: q.question_text || q.question || '',
          options: q.options || [],
          correct_option: q.correct_option || q.correctOption || 'A',
          explanation: q.explanation || '',
          year: parseInt(q.year || 2026, 10)
        };
        const localQ = JSON.parse(localStorage.getItem('ZIGLAG_CUSTOM_QUESTIONS') || '[]');
        localQ.unshift(payload);
        localStorage.setItem('ZIGLAG_CUSTOM_QUESTIONS', JSON.stringify(localQ));
        return payload;
      },

      
      delete: async function (qId) {
        try {
          await apiRequest(`/api/questions/${encodeURIComponent(qId)}`, 'DELETE');
        } catch (e) {}
        let localQ = JSON.parse(localStorage.getItem('ZIGLAG_CUSTOM_QUESTIONS') || '[]');
        localQ = localQ.filter(q => q.id !== qId);
        localStorage.setItem('ZIGLAG_CUSTOM_QUESTIONS', JSON.stringify(localQ));
        return true;
      },

      export: async function () {
        try {
          return await apiRequest('/api/questions/export');
        } catch (e) {
          const list = await this.list('');
          return { app: 'PrepCBT', questions: list };
        }
      },

      import: async function (data) {
        try {
          return await apiRequest('/api/questions/import', 'POST', data);
        } catch (e) {
          return { success: true };
        }
      },

      bulkInsert: async function (qList) {
        try {
          const res = await apiRequest('/api/questions/bulk', 'POST', qList);
          if (res.success) return res;
        } catch (e) {
          console.warn('[ZiglagDB] Bulk insert API error, saving locally:', e);
        }

        for (const item of qList) {
          await this.create(item);
        }
        return { success: true, count: qList.length };
      }
    },

    courses: {
      list: async function () {
        try {
          const list = await apiRequest('/api/courses');
          if (list && list.length > 0) return list;
        } catch (e) {
          console.warn('[ZiglagDB] Courses API notice, using fallback:', e);
        }

        return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_COURSES') || JSON.stringify([
          {
            id: 'jamb-prep',
            title: 'JAMB / Post-JAMB Comprehensive Prep',
            slug: 'jamb-prep',
            category: 'JAMB / Post-JAMB',
            description: 'High-yield masterclass on Calculus, Coordinate Geometry, Projectile Motion, Stoichiometry, and Mechanics.',
            icon: '🎯',
            badge: 'Bestseller',
            instructor: 'Mr. Isaac Olusola',
            display_order: 1
          },
          {
            id: 'calculus-essentials',
            title: 'Calculus Essentials & Advanced Methods',
            slug: 'calculus-essentials',
            category: 'Senior Secondary WASSCE',
            description: 'From limits and first-principles differentiation to definite integrals and kinematic applications.',
            icon: '∫',
            badge: 'Advanced',
            instructor: 'Mr. Isaac Olusola',
            display_order: 2
          },
          {
            id: 'physics-mechanics',
            title: 'Classical Mechanics & Wave Optics',
            slug: 'physics-mechanics',
            category: 'Senior Secondary WASSCE',
            description: 'Vectors, Newton laws of motion, rotational dynamics, SHM, and geometric optics with exam past papers.',
            icon: '⚡',
            badge: 'Core STEM',
            instructor: 'Mr. Isaac Olusola',
            display_order: 3
          }
        ]));
      },

      create: async function (courseData) {
        return await this.save(courseData);
      },

      save: async function (courseData) {
        try {
          const res = await apiRequest('/api/courses', 'POST', courseData);
          if (res.success) return res.course;
        } catch (e) {
          console.warn('[ZiglagDB] Save course API error, saving locally:', e);
        }

        const list = await this.list();
        const payload = {
          id: courseData.id || ('course_' + Date.now()),
          title: courseData.title,
          slug: courseData.slug || courseData.title.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
          category: courseData.category || 'exams',
          subcategory: courseData.subcategory || courseData.subcat || 'General',
          description: courseData.description || '',
          icon: courseData.icon || '📐',
          badge: courseData.badge || 'Comprehensive',
          instructor: courseData.instructor || 'Mr. Isaac Olusola',
          duration_weeks: parseInt(courseData.duration_weeks || 6, 10),
          syllabus: courseData.syllabus || [],
          display_order: parseInt(courseData.display_order || 0, 10)
        };
        list.push(payload);
        localStorage.setItem('ZIGLAG_LOCAL_COURSES', JSON.stringify(list));
        return payload;
      },
      delete: async function (courseId) {
        try {
          const res = await apiRequest(`/api/courses/${encodeURIComponent(courseId)}`, 'DELETE');
          if (res.success) return true;
        } catch (e) {
          console.warn('[ZiglagDB] Delete course API notice:', e);
        }
        let list = await this.list();
        list = list.filter(c => c.id !== courseId);
        localStorage.setItem('ZIGLAG_LOCAL_COURSES', JSON.stringify(list));
        return true;
      }
    },

    lectures: {
      listByCourse: async function (courseId) {
        try {
          const url = (courseId && String(courseId).trim()) ? `/api/lectures?course_id=${encodeURIComponent(courseId)}` : '/api/lectures';
          const list = await apiRequest(url);
          if (list && list.length > 0) return list;
        } catch (e) {
          console.warn('[ZiglagDB] Lectures fetch API error, checking local:', e);
        }

        return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_LECTURES_' + courseId) || '[]');
      },

      create: async function (lectureData) {
        return await this.save(lectureData);
      },

      save: async function (lectureData) {
        const normUrl = window.ZiglagDB.utils.normalizeVideoUrl(lectureData.video_url || lectureData.videoUrl || '');
        const topicCat = lectureData.topic_category || lectureData.group || lectureData.topic || 'General';
        const payloadData = {
          ...lectureData,
          topic_category: topicCat,
          group: topicCat,
          topic: topicCat,
          video_url: normUrl
        };
        try {
          const res = await apiRequest('/api/lectures', 'POST', payloadData);
          if (res.success) return res.lecture;
        } catch (e) {
          console.warn('[ZiglagDB] Save lecture API error, saving locally:', e);
        }

        const payload = {
          id: lectureData.id || ('lec_' + Date.now()),
          course_id: lectureData.course_id || lectureData.courseId,
          title: lectureData.title,
          topic_category: topicCat,
          group: topicCat,
          topic: topicCat,
          video_url: normUrl,
          duration: lectureData.duration || '30 mins',
          order_index: parseInt(lectureData.order_index || 1, 10),
          notes_url: lectureData.notes_url || '',
          description: lectureData.description || ''
        };
        const key = 'ZIGLAG_LOCAL_LECTURES_' + payload.course_id;
        const list = JSON.parse(localStorage.getItem(key) || '[]');
        list.push(payload);
        localStorage.setItem(key, JSON.stringify(list));
        return payload;
      },

      delete: async function (lectureId, courseId) {
        try {
          const res = await apiRequest('/api/lectures/' + encodeURIComponent(lectureId), 'DELETE');
          if (res && res.success) return true;
        } catch (e) {
          console.warn('[ZiglagDB] Delete lecture API notice:', e)
        }
        if (courseId) {
          const key = 'ZIGLAG_LOCAL_LECTURES_' + courseId;
          let list = JSON.parse(localStorage.getItem(key) || '[]');
          list = list.filter(l => l.id !== lectureId);
          localStorage.setItem(key, JSON.stringify(list));
        }
        return true;
      }
    },

    vault: {
      list: async function () {
        try {
          const list = await apiRequest('/api/vault');
          if (list && list.length > 0) return list;
        } catch (e) {
          console.warn('[ZiglagDB] Vault API error, using local fallback:', e);
        }

        return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_VAULT') || JSON.stringify([
          {
            id: 'res-jamb-math-formulas',
            title: 'Complete JAMB Mathematics Formula Sheet & Shortcuts',
            category: 'JAMB UTME',
            file_url: '#',
            file_size: '2.4 MB',
            badge: 'PDF',
            description: 'Comprehensive compilation of all formulas in Algebra, Calculus, Matrices, and Trigonometry.'
          },
          {
            id: 'res-waec-physics-mechanics',
            title: 'WASSCE Physics Mechanics & Motion Mastery Guide',
            category: 'WASSCE / NECO',
            file_url: '#',
            file_size: '3.1 MB',
            badge: 'PDF',
            description: 'Detailed breakdown of projectile motion, friction, momentum conservation, and solved WAEC past questions.'
          }
        ]));
      },

      create: async function (item) {
        return await this.save(item);
      },

      save: async function (item) {
        try {
          const res = await apiRequest('/api/vault', 'POST', item);
          if (res.success) return res.resource;
        } catch (e) {
          console.warn('[ZiglagDB] Save vault resource API error, saving locally:', e);
        }

        const list = await this.list();
        const payload = {
          id: item.id || ('res_' + Date.now()),
          title: item.title,
          category: item.category || 'exams',
          subcategory: item.subcategory || item.subcat || 'General',
          file_url: item.file_url || '#',
          file_size: item.file_size || '1.5 MB',
          badge: item.badge || 'PDF Bundle',
          description: item.description || ''
        };
        list.unshift(payload);
        localStorage.setItem('ZIGLAG_LOCAL_VAULT', JSON.stringify(list));
        return payload;
      },
      delete: async function (resourceId) {
        try {
          const res = await apiRequest(`/api/vault/${encodeURIComponent(resourceId)}`, 'DELETE');
          if (res.success) return true;
        } catch (e) {
          console.warn('[ZiglagDB] Delete vault resource notice:', e);
        }
        let list = await this.list();
        list = list.filter(r => r.id !== resourceId);
        localStorage.setItem('ZIGLAG_LOCAL_VAULT', JSON.stringify(list));
        return true;
      },
      uploadPdf: async function (file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/upload/pdf', {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ message: 'Upload failed' }));
          throw new Error(err.message || 'File upload error');
        }
        return await res.json();
      }
    },
    people: {
      get: async function () {
        try {
          const list = await apiRequest('/api/people');
          if (list && list.length > 0) return list;
        } catch (e) {}
        return [{
          name: 'Isaac Olusola',
          role: 'Founder & Lead Applied Mathematician',
          bio: 'Applied Mathematician and curriculum architect dedicated to demystifying advanced mathematics.',
          avatar: 'IMG_1399.JPG',
          email: 'ziglaginstitute@gmail.com',
          linkedin: 'https://www.linkedin.com/in/isaac-olusola-2a2b2218b',
          github: 'https://github.com/ziglaginstitute-del',
          youtube: 'https://youtube.com/@ziglaginstitute?si=pb96DBtz9CQRfpbn'
        }];
      },
      update: async function (profileData) {
        return await apiRequest('/api/people/update', 'POST', profileData);
      }
    },
    contact: {
      listSubmissions: async function () {
        try {
          return await apiRequest('/api/contact/submissions');
        } catch (e) {
          return [];
        }
      },
      deleteSubmission: async function (subId) {
        return await apiRequest(`/api/contact/submissions/${subId}`, 'DELETE');
      }
    },
    tutoring: {
      book: async function (bookingData) {
        try {
          const res = await apiRequest('/api/tutoring/book', 'POST', bookingData);
          if (res && res.success) return res;
        } catch (e) {
          console.warn('[ZiglagDB] Tutoring booking API warning, saving locally:', e);
        }

        const payload = {
          id: bookingData.id || ('book_' + Date.now()),
          ...bookingData,
          status: 'Confirmed',
          created_at: new Date().toISOString()
        };
        const list = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_BOOKINGS') || '[]');
        list.unshift(payload);
        localStorage.setItem('ZIGLAG_LOCAL_BOOKINGS', JSON.stringify(list));
        return { success: true, booking: payload, localFallback: true };
      },

      listBookings: async function () {
        try {
          const list = await apiRequest('/api/tutoring/bookings');
          if (list && Array.isArray(list)) return list;
        } catch (e) {
          console.warn('[ZiglagDB] List tutoring bookings API warning:', e);
        }
        return JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_BOOKINGS') || '[]');
      },

      deleteBooking: async function (bookingId) {
        try {
          const res = await apiRequest('/api/tutoring/bookings/' + encodeURIComponent(bookingId), 'DELETE');
          if (res && res.success) return true;
        } catch (e) {
          console.warn('[ZiglagDB] Delete tutoring booking API warning:', e);
        }
        let list = JSON.parse(localStorage.getItem('ZIGLAG_LOCAL_BOOKINGS') || '[]');
        list = list.filter(b => b.id !== bookingId);
        localStorage.setItem('ZIGLAG_LOCAL_BOOKINGS', JSON.stringify(list));
        return true;
      }
    },

    siteContent: {
      get: async function () {
        try {
          return await apiRequest('/api/site-content');
        } catch (e) {
          return {};
        }
      },
      save: async function (data) {
        return await apiRequest('/api/site-content', 'POST', data);
      }
    },

    // Community Math & Physics Q&A Hub
    community: {
      _getFallbackQuestions: function () {
        let stored = localStorage.getItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS');
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            if (Array.isArray(parsed) && parsed.length > 0) return parsed;
          } catch (e) { }
        }
        const seeds = [
          {
            id: "cq_seed_01",
            title: "Conversion of Fractional Decimal Numbers to Binary (Base 2)",
            subject: "Mathematics",
            difficulty: "Beginner",
            content_latex: "What is the exact procedure for converting decimal fractions into binary base 2? For example:\n$$13.625_{10} = (?)_{2}$$\nI understand how to convert the integer part $13_{10}$, but the fractional part $.625$ always confuses me.",
            author_name: "Chukwudi Eze",
            author_email: "chukwudi.eze@example.com",
            views: 42,
            upvotes: 7,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
            answers: [
              {
                id: "ans_seed_01",
                question_id: "cq_seed_01",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 18,
                created_at: new Date(Date.now() - 86400000 * 2.8).toISOString(),
                content_latex: "To convert a fractional decimal number like $13.625_{10}$ to binary, decompose it into its **integer part** ($13$) and **fractional part** ($0.625$).\n\n### Step 1: Integer Part by Repeated Division by 2\n$$13 \\div 2 = 6 \\text{ rem } 1$$\n$$6 \\div 2 = 3 \\text{ rem } 0$$\n$$3 \\div 2 = 1 \\text{ rem } 1$$\n$$1 \\div 2 = 0 \\text{ rem } 1$$\nReading remainders bottom-up gives: $$13_{10} = 1101_2$$\n\n### Step 2: Fractional Part by Repeated Multiplication by 2\nMultiply the fraction by 2 and record the integer carry:\n$$0.625 \\times 2 = 1.250 \\rightarrow \\text{record } 1, \\text{ remainder } 0.250$$\n$$0.250 \\times 2 = 0.500 \\rightarrow \\text{record } 0, \\text{ remainder } 0.500$$\n$$0.500 \\times 2 = 1.000 \\rightarrow \\text{record } 1, \\text{ remainder } 0.000 \\text{ (terminates)}$$\nReading integers top-down gives: $$0.625_{10} = 0.101_2$$\n\n### Step 3: Combine\n$$13.625_{10} = 1101.101_2$$\nThis is an essential question type in JAMB, WASSCE General Mathematics, and Computer Studies."
              }
            ]
          },
          {
            id: "cq_seed_02",
            title: "Uniform Acceleration Kinematics (JAMB / WASSCE Physics)",
            subject: "Physics",
            difficulty: "Beginner",
            content_latex: "A vehicle starts from rest ($u = 0$) and accelerates uniformly to a final velocity of $v = 25\\text{ m/s}$ in $t = 10\\text{ s}$. How do we compute the total displacement $s$ using kinematic equations?",
            author_name: "Blessing Okon",
            author_email: "blessing.okon@example.com",
            views: 35,
            upvotes: 5,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000 * 2.5).toISOString(),
            answers: [
              {
                id: "ans_seed_02",
                question_id: "cq_seed_02",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 12,
                created_at: new Date(Date.now() - 86400000 * 2.3).toISOString(),
                content_latex: "### Given Parameters:\n- Initial velocity $u = 0\\text{ m/s}$\n- Final velocity $v = 25\\text{ m/s}$\n- Time $t = 10\\text{ s}$\n\n### Method 1: Average Velocity Formula\n$$s = \\left(\\frac{u + v}{2}\\right) t$$\n$$s = \\left(\\frac{0 + 25}{2}\\right) \\times 10 = 12.5 \\times 10 = 125\\text{ meters}$$\n\n### Method 2: Via Acceleration $a$\n$$a = \\frac{v - u}{t} = \\frac{25 - 0}{10} = 2.5\\text{ m/s}^2$$\n$$s = ut + \\frac{1}{2}at^2 = (0)(10) + \\frac{1}{2}(2.5)(10^2) = 0.5 \\times 2.5 \\times 100 = 125\\text{ meters}$$\nBoth kinematic approaches yield $125\\text{ m}$."
              }
            ]
          },
          {
            id: "cq_seed_03",
            title: "Proof of Alternate Segment Theorem in Circle Geometry (WASSCE / IGCSE)",
            subject: "Mathematics",
            difficulty: "Intermediate",
            content_latex: "In circle geometry, prove that the angle between a tangent to a circle and a chord drawn through the point of contact is equal to the angle subtended by the chord in the alternate segment:\n$$\\angle TAB = \\angle ACB$$\nHow do we prove this formally for WAEC / Cambridge exam marks?",
            author_name: "Faruk Danjuma",
            author_email: "faruk.danjuma@example.com",
            views: 68,
            upvotes: 14,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
            answers: [
              {
                id: "ans_seed_03",
                question_id: "cq_seed_03",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 24,
                created_at: new Date(Date.now() - 86400000 * 1.8).toISOString(),
                content_latex: "### Formal Proof:\n1. Draw circle with center $O$ and tangent line $TAT'$ contacting at $A$.\n2. Draw diameter $AOD$ through $O$ to point $D$ on the circumference, and connect $DB$.\n3. Since tangent $TAT' \\perp$ radius $OA$:\n$$\\angle TAD = 90^\\circ$$\n$$\\angle TAB = \\angle TAD - \\angle DAB = 90^\\circ - \\angle DAB$$\n4. In $\\triangle ABD$, angle in a semicircle is $90^\\circ$, so $\\angle ABD = 90^\\circ$.\nSum of angles in $\\triangle ABD$:\n$$\\angle ADB = 180^\\circ - 90^\\circ - \\angle DAB = 90^\\circ - \\angle DAB$$\n5. Therefore: $$\\angle TAB = \\angle ADB$$\n6. Angles subtended by the same chord $AB$ in the same segment are equal: $$\\angle ADB = \\angle ACB$$\n7. By transitivity: $$\\angle TAB = \\angle ACB \\quad \\text{Q.E.D.}$$"
              }
            ]
          },
          {
            id: "cq_seed_04",
            title: "Derivation of Maximum Horizontal Range in Projectile Motion",
            subject: "Physics",
            difficulty: "Intermediate",
            content_latex: "For a projectile launched at speed $u$ and angle $\\theta$ to the horizontal over level ground, prove that the horizontal range is:\n$$R = \\frac{u^2 \\sin(2\\theta)}{g}$$\nand show that the maximum range occurs at $\\theta = 45^\\circ$.",
            author_name: "Amara Nwachukwu",
            author_email: "amara.n@example.com",
            views: 53,
            upvotes: 11,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000 * 1.5).toISOString(),
            answers: [
              {
                id: "ans_seed_04",
                question_id: "cq_seed_04",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 21,
                created_at: new Date(Date.now() - 86400000 * 1.2).toISOString(),
                content_latex: "### Derivation:\nVelocity components:\n$$u_x = u \\cos\\theta, \\quad u_y = u \\sin\\theta$$\nTotal time of flight $T$ (setting vertical displacement $y = 0$):\n$$0 = u_y T - \\frac{1}{2}g T^2 \\implies T = \\frac{2u \\sin\\theta}{g}$$\nHorizontal displacement $R$:\n$$R = u_x \\times T = (u \\cos\\theta)\\left(\\frac{2u \\sin\\theta}{g}\\right) = \\frac{u^2 (2\\sin\\theta \\cos\\theta)}{g}$$\nUsing double-angle identity $2\\sin\\theta \\cos\\theta = \\sin(2\\theta)$:\n$$R = \\frac{u^2 \\sin(2\\theta)}{g}$$\n\n### Maximum Range:\n$R$ is maximized when $\\sin(2\\theta)$ reaches its absolute maximum of $1$:\n$$\\sin(2\\theta) = 1 \\implies 2\\theta = 90^\\circ \\implies \\theta = 45^\\circ$$\n$$R_{\\max} = \\frac{u^2}{g}$$"
              }
            ]
          },
          {
            id: "cq_seed_05",
            title: "Eigenvalues and Orthonormal Eigenspaces of a 3x3 Symmetric Tridiagonal Matrix",
            subject: "Mathematics",
            difficulty: "Advanced",
            content_latex: "Let $A$ be the symmetric matrix:\n$$A = \\begin{pmatrix} 2 & 1 & 0 \\\\ 1 & 2 & 1 \\\\ 0 & 1 & 2 \\end{pmatrix}$$\nFind all eigenvalues $\\lambda_1, \\lambda_2, \\lambda_3$ and determine an orthonormal basis of eigenvectors for $\\mathbb{R}^3$.",
            author_name: "Kelechi Adeleke",
            author_email: "kelechi.adeleke@example.com",
            views: 89,
            upvotes: 19,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000).toISOString(),
            answers: [
              {
                id: "ans_seed_05",
                question_id: "cq_seed_05",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 31,
                created_at: new Date(Date.now() - 86400000 * 0.8).toISOString(),
                content_latex: "### Step 1: Characteristic Polynomial\n$$\\det(A - \\lambda I) = \\begin{vmatrix} 2-\\lambda & 1 & 0 \\\\ 1 & 2-\\lambda & 1 \\\\ 0 & 1 & 2-\\lambda \\end{vmatrix} = 0$$\nLet $\\mu = 2 - \\lambda$. Then:\n$$\\det = \\mu(\\mu^2 - 1) - 1(\\mu) = \\mu(\\mu^2 - 2) = 0$$\n$$\\mu = 0 \\quad \\text{or} \\quad \\mu = \\pm\\sqrt{2}$$\n\nSubstituting back $\\lambda = 2 - \\mu$:\n$$\\lambda_1 = 2 + \\sqrt{2}, \\quad \\lambda_2 = 2, \\quad \\lambda_3 = 2 - \\sqrt{2}$$\n\n### Step 2: Orthonormal Eigenvectors\n- For $\\lambda_2 = 2$ ($\\\\mu = 0$): $\\vec{v}_2 = \\frac{1}{\\sqrt{2}}\\begin{pmatrix} 1 \\\\ 0 \\\\ -1 \\end{pmatrix}$\n- For $\\lambda_1 = 2 + \\sqrt{2}$: $\\vec{v}_1 = \\frac{1}{2}\\begin{pmatrix} 1 \\\\ \\sqrt{2} \\\\ 1 \\end{pmatrix}$\n- For $\\lambda_3 = 2 - \\sqrt{2}$: $\\vec{v}_3 = \\frac{1}{2}\\begin{pmatrix} 1 \\\\ -\\sqrt{2} \\\\ 1 \\end{pmatrix}$\nBecause $A$ is symmetric, all eigenvectors are mutually orthogonal and form an orthonormal basis."
              }
            ]
          },
          {
            id: "cq_seed_06",
            title: "Infinite Square Well: Solving the Time-Independent Schrödinger Equation",
            subject: "Physics",
            difficulty: "Advanced",
            content_latex: "Consider a particle of mass $m$ confined to a 1D box with potential:\n$$V(x) = \\begin{cases} 0 & \\text{for } 0 \\le x \\le L \\\\ \\infty & \\text{otherwise} \\end{cases}$$\nDerive the normalized stationary wavefunctions $\\psi_n(x)$ and energy levels $E_n$ from the Schrödinger equation.",
            author_name: "Toluwani Alao",
            author_email: "toluwani.alao@example.com",
            views: 74,
            upvotes: 15,
            status: "Solved",
            answers_count: 1,
            has_educator_answer: true,
            created_at: new Date(Date.now() - 86400000 * 0.5).toISOString(),
            answers: [
              {
                id: "ans_seed_06",
                question_id: "cq_seed_06",
                author_name: "Mr. Isaac Olusola",
                author_email: "ziglaginstitute@gmail.com",
                is_educator: true,
                is_verified: true,
                upvotes: 27,
                created_at: new Date(Date.now() - 86400000 * 0.3).toISOString(),
                content_latex: "### Formulation & Solution:\nInside the well ($0 < x < L$), $V(x) = 0$, so the 1D Schrödinger equation is:\n$$-\\frac{\\hbar^2}{2m} \\frac{d^2\\psi}{dx^2} = E\\psi \\implies \\frac{d^2\\psi}{dx^2} + k^2\\psi = 0, \\quad k = \\frac{\\sqrt{2mE}}{\\hbar}$$\nGeneral solution:\n$$\\psi(x) = A \\sin(kx) + B \\cos(kx)$$\n\n### Boundary Conditions:\n- At $x = 0$: $\\psi(0) = B = 0$\n- At $x = L$: $\\psi(L) = A \\sin(kL) = 0 \\implies kL = n\\pi, \\quad n \\in \\{1, 2, 3, \\dots\\}$\n\n### Quantized Energies:\n$$k_n = \\frac{n\\pi}{L} \\implies E_n = \\frac{\\hbar^2 k_n^2}{2m} = \\frac{n^2 \\pi^2 \\hbar^2}{2m L^2} = \\frac{n^2 h^2}{8m L^2}$$\n\n### Normalization:\n$$\\int_0^L |\\psi_n(x)|^2 dx = 1 \\implies A^2 \\int_0^L \\sin^2\\left(\\frac{n\\pi x}{L}\\right) dx = A^2 \\left(\\frac{L}{2}\\right) = 1 \\implies A = \\sqrt{\\frac{2}{L}}$$\n$$\\psi_n(x) = \\sqrt{\\frac{2}{L}} \\sin\\left(\\frac{n\\pi x}{L}\\right)$$"
              }
            ]
          }
        ];
        try {
          localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(seeds));
        } catch (e) { }
        return seeds;
      },

      listQuestions: async function (filters = {}) {
        const params = new URLSearchParams();
        if (filters.difficulty && filters.difficulty !== 'all') params.append('difficulty', filters.difficulty);
        if (filters.subject && filters.subject !== 'all') params.append('subject', filters.subject);
        if (filters.status && filters.status !== 'all') params.append('status', filters.status);
        if (filters.search) params.append('search', filters.search);

        const url = `/api/community/questions${params.toString() ? '?' + params.toString() : ''}`;
        try {
          return await apiRequest(url);
        } catch (e) {
          console.warn('[ZiglagDB] Community questions API failed, using local fallback:', e);
          let questions = this._getFallbackQuestions();
          if (filters.difficulty && filters.difficulty !== 'all') {
            questions = questions.filter(q => (q.difficulty || '').toLowerCase() === filters.difficulty.toLowerCase());
          }
          if (filters.subject && filters.subject !== 'all') {
            questions = questions.filter(q => (q.subject || '').toLowerCase() === filters.subject.toLowerCase());
          }
          if (filters.status && filters.status !== 'all') {
            questions = questions.filter(q => (q.status || '').toLowerCase() === filters.status.toLowerCase());
          }
          if (filters.search) {
            const s = filters.search.toLowerCase();
            questions = questions.filter(q => (q.title || '').toLowerCase().includes(s) || (q.content_latex || '').toLowerCase().includes(s));
          }
          return questions;
        }
      },

      getQuestion: async function (questionId) {
        try {
          const res = await apiRequest(`/api/community/questions/${questionId}`);
          return res.question;
        } catch (e) {
          console.warn('[ZiglagDB] Get question detail failed:', e);
          const questions = this._getFallbackQuestions();
          return questions.find(q => q.id === questionId) || null;
        }
      },

      askQuestion: async function (data) {
        try {
          const res = await apiRequest('/api/community/questions', 'POST', data);
          return res;
        } catch (e) {
          console.warn('[ZiglagDB] Ask question API failed, saving locally:', e);
          const qid = `cq_local_${Date.now()}`;
          const newQ = {
            id: qid,
            title: data.title,
            subject: data.subject || 'Mathematics',
            difficulty: data.difficulty || 'Intermediate',
            content_latex: data.content_latex || data.content,
            author_name: data.author_name || 'Student Scholar',
            author_email: data.author_email || '',
            attachment_url: data.attachment_url || '',
            attachment_name: data.attachment_name || '',
            attachment_type: data.attachment_type || '',
            views: 1,
            upvotes: 0,
            status: 'Open',
            answers_count: 0,
            has_educator_answer: false,
            created_at: new Date().toISOString(),
            answers: []
          };
          const questions = this._getFallbackQuestions();
          questions.unshift(newQ);
          try {
            localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(questions));
          } catch (e) { }
          return { success: true, question: newQ, offline: true };
        }
      },

      postAnswer: async function (questionId, data) {
        try {
          const res = await apiRequest(`/api/community/questions/${questionId}/answers`, 'POST', data);
          return res;
        } catch (e) {
          console.warn('[ZiglagDB] Post answer API failed, saving locally:', e);
          const aid = `ans_local_${Date.now()}`;
          const isEducator = (data.author_email && data.author_email.toLowerCase() === 'ziglaginstitute@gmail.com') ||
            (data.author_name && data.author_name.toLowerCase().includes('isaac olusola'));
          const newAns = {
            id: aid,
            question_id: questionId,
            author_name: isEducator ? 'Mr. Isaac Olusola' : (data.author_name || 'Community Scholar'),
            author_email: data.author_email || '',
            is_educator: !!isEducator,
            is_verified: !!isEducator,
            content_latex: data.content_latex || data.content,
            attachment_url: data.attachment_url || '',
            attachment_name: data.attachment_name || '',
            attachment_type: data.attachment_type || '',
            upvotes: 0,
            created_at: new Date().toISOString()
          };
          const questions = this._getFallbackQuestions();
          const targetQ = questions.find(q => q.id === questionId);
          if (targetQ) {
            targetQ.answers = targetQ.answers || [];
            targetQ.answers.push(newAns);
            targetQ.answers_count = targetQ.answers.length;
            if (isEducator) {
              targetQ.status = 'Solved';
              targetQ.has_educator_answer = true;
            }
            try {
              localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(questions));
            } catch (e) { }
          }
          return { success: true, answer: newAns, offline: true };
        }
      },

      upvoteQuestion: async function (questionId) {
        try {
          return await apiRequest(`/api/community/questions/${questionId}/upvote`, 'POST');
        } catch (e) {
          console.warn('[ZiglagDB] Upvote question API failed, updating locally:', e);
          const questions = this._getFallbackQuestions();
          const q = questions.find(item => item.id === questionId);
          let count = 1;
          if (q) {
            q.upvotes = (q.upvotes || 0) + 1;
            count = q.upvotes;
            try {
              localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(questions));
            } catch (e) { }
          }
          return { success: true, upvotes: count, offline: true };
        }
      },

      upvoteAnswer: async function (answerId) {
        try {
          return await apiRequest(`/api/community/answers/${answerId}/upvote`, 'POST');
        } catch (e) {
          console.warn('[ZiglagDB] Upvote answer API failed, updating locally:', e);
          const questions = this._getFallbackQuestions();
          let count = 1;
          for (const q of questions) {
            if (q.answers) {
              const a = q.answers.find(ans => ans.id === answerId);
              if (a) {
                a.upvotes = (a.upvotes || 0) + 1;
                count = a.upvotes;
                break;
              }
            }
          }
          try {
            localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(questions));
          } catch (e) { }
          return { success: true, upvotes: count, offline: true };
        }
      },

      uploadAttachment: async function (file) {
        const formData = new FormData();
        formData.append('file', file);
        const baseUrl = getApiBaseUrl();
        try {
          const res = await fetch(`${baseUrl}/api/community/upload`, {
            method: 'POST',
            body: formData
          });
          if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Upload error (${res.status}): ${errText}`);
          }
          return await res.json();
        } catch (e) {
          console.warn('[ZiglagDB] Server upload failed, falling back to client-side data URL:', e);
          return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => {
              const isPdf = file.type === 'application/pdf' || file.name.endsWith('.pdf');
              resolve({
                success: true,
                file_url: reader.result,
                file_name: file.name,
                file_size: (file.size / 1024).toFixed(1) + ' KB',
                file_type: isPdf ? 'pdf' : 'image',
                offline: true
              });
            };
            reader.readAsDataURL(file);
          });
        }
      },

      deleteQuestion: async function (questionId) {
        try {
          return await apiRequest(`/api/community/questions/${questionId}`, 'DELETE');
        } catch (e) {
          console.warn('[ZiglagDB] Delete question API failed:', e);
          let questions = this._getFallbackQuestions();
          questions = questions.filter(q => q.id !== questionId);
          try {
            localStorage.setItem('ZIGLAG_LOCAL_COMMUNITY_QUESTIONS', JSON.stringify(questions));
          } catch (e) { }
          return { success: true };
        }
      },

      deleteAnswer: async function (answerId) {
        try {
          return await apiRequest(`/api/community/answers/${answerId}`, 'DELETE');
        } catch (e) {
          console.warn('[ZiglagDB] Delete answer API failed:', e);
          return { success: true };
        }
      }
    },

    // Neon Cloud Services Integration (Postgres, Auth, AI, Functions, Realtime)
    neon: {
      getServices: async function () {
        try {
          return await apiRequest('/api/neon/services');
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      auth: {
        getConfig: async function () {
          return await apiRequest('/api/neon/auth/config');
        }
      },
      ai: {
        getModels: async function () {
          return await apiRequest('/api/neon/ai/models');
        },
        askMathAssistant: async function (question, model) {
          return await apiRequest('/api/neon/ai/math-assistant', 'POST', { question, model });
        }
      },
      functions: {
        invoke: async function (name = 'hello') {
          return await apiRequest(`/api/neon/functions/invoke?name=${encodeURIComponent(name)}`);
        }
      },
      realtime: {
        getInfo: async function () {
          return await apiRequest('/api/neon/realtime/info');
        }
      }
    }
  };

  window.ZiglagDB = ZiglagDB;
  window.normalizeVideoUrl = function (url) {
    return ZiglagDB.utils ? ZiglagDB.utils.normalizeVideoUrl(url) : (url || "");
  };
})(window);
