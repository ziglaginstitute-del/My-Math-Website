/**
 * Ziglag Institute Math Portal - Universal Database Layer
 * Completely independent of Supabase.
 * Connects directly to backend database (Local SQLite or Cloud PostgreSQL/Neon)
 * with graceful offline local-storage fallback.
 */

(function (window) {
  'use strict';

  // API helper
  async function apiRequest(endpoint, method = 'GET', body = null) {
    const opts = {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      opts.body = JSON.stringify(body);
    }
    const response = await fetch(endpoint, opts);
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
          const list = await apiRequest(`/api/lectures?course_id=${encodeURIComponent(courseId)}`);
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
        const payloadData = {
          ...lectureData,
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
          avatar: '👨‍🏫',
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
