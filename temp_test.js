
    // Vault Logic Controller
    document.addEventListener("DOMContentLoaded", () => {
      renderVault();
    });

    function renderVault() {
      const grid = document.getElementById("vault-render-grid");
      const searchVal = document.getElementById("vault-search-input").value.toLowerCase();
      const catVal = document.querySelector('input[name="vault-cat"]:checked').value;
      
      const subAp = document.getElementById("sub-ap").checked;
      const subIgcse = document.getElementById("sub-igcse").checked;
      const subGcse = document.getElementById("sub-gcse").checked;
      const subWassce = document.getElementById("sub-wassce").checked;
      const subJamb = document.getElementById("sub-jamb").checked;
      const subGce = document.getElementById("sub-gce").checked;
      const hasSubSelection = subAp || subIgcse || subGcse || subWassce || subJamb || subGce;
      
      grid.innerHTML = "";
      
      const filtered = MATH_DATABASE.vault.filter(v => {
        // Keyword Search
        if (searchVal && !v.title.toLowerCase().includes(searchVal) && !v.subcat.toLowerCase().includes(searchVal)) {
          return false;
        }
        
        // Category Search
        if (catVal !== "all" && v.category !== catVal) {
          return false;
        }
        
        // Subcat check
        if (hasSubSelection) {
          const matchAp = subAp && v.subcat === "AP MATHS";
          const matchIgcse = subIgcse && v.subcat === "IGCSE";
          const matchGcse = subGcse && v.subcat === "GCSE";
          const matchWassce = subWassce && v.subcat === "WASSCE";
          const matchJamb = subJamb && v.subcat === "JAMB";
          const matchGce = subGce && v.subcat === "GCE";
          
          if (!matchAp && !matchIgcse && !matchGcse && !matchWassce && !matchJamb && !matchGce) return false;
        }
        
        return true;
      });

      document.getElementById("vault-count").innerText = filtered.length;

      if (filtered.length === 0) {
        grid.innerHTML = `
          <div class="glass-card" style="grid-column:1/-1; text-align:center; padding:3rem;">
            <h3>No pdf documents found</h3>
            <p style="margin-top:0.5rem;">Try unchecking subcategory filters or broadening search words.</p>
          </div>
        `;
        return;
      }

      filtered.forEach(v => {
        const card = document.createElement("div");
        card.className = "sphere-card glass-card";
        card.style.animation = "slide-up 0.5s ease-out";
        
        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem; align-items:center;">
              <span style="font-size:2rem;">📕</span>
              <span class="sphere-tag" style="color:var(--accent-color); border-color:var(--border-highlight); background:rgba(6,182,212,0.06); font-weight:700;">
                ${v.type}
              </span>
            </div>
            <h3 style="font-size:1.15rem; margin-bottom:0.5rem; line-height:1.4;">${v.title}</h3>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:1.5rem;">Subcategory: <strong style="color:var(--text-main);">${v.subcat}</strong></p>
          </div>
          
          <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-color); padding-top:0.75rem;">
            <span style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">${v.size}</span>
            <button class="btn btn-primary btn-sm" onclick="openPdfModal('${v.id}')">View Document ➜</button>
          </div>
        `;
        
        grid.appendChild(card);
      });
    }

    function filterVault() {
      renderVault();
    }

    let activePdfDoc = null;

    // Modal PDF previews
    function openPdfModal(vaultId) {
      const doc = MATH_DATABASE.vault.find(v => v.id === vaultId);
      if (!doc) return;
      activePdfDoc = doc;
      
      document.getElementById("pdf-modal-title").innerText = doc.title;
      document.getElementById("pdf-modal-meta").innerText = `${doc.type.toUpperCase()} • ${doc.size}`;
      
      const scrollContent = document.getElementById("pdf-scroll-content");
      if (doc.fileUrl) {
        // Clear padding and inject a full-height iframe to render the actual PDF or Google Drive doc
        scrollContent.style.padding = "0";
        let targetDocUrl = doc.fileUrl;
        if (targetDocUrl.includes("drive.google.com") && targetDocUrl.includes("/view")) {
          targetDocUrl = targetDocUrl.replace(/\/view.*/, "/preview");
        }
        scrollContent.innerHTML = `<iframe src="${targetDocUrl}" style="width:100%; height:100%; border:none; background:#181F30;" title="${doc.title}"></iframe>`;
      } else {
        // Reset default padding and inject the beautifully styled placeholder page mockup
        scrollContent.style.padding = "3rem 2rem";
        scrollContent.innerHTML = `
          <!-- Styled PDF Page 1 mockup -->
          <div class="glass-card" style="width:100%; max-width:600px; min-height:800px; background:white; color:#0f172a; padding:4rem 3rem; box-shadow:0 10px 30px rgba(0,0,0,0.5); display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div style="display:flex; justify-content:space-between; border-bottom:2px solid #4f46e5; padding-bottom:1rem; margin-bottom:2rem;">
                <span style="font-weight:800; font-size:1.1rem; color:#4f46e5;">ZIGLAG INSTITUTE vault</span>
                <span style="font-size:0.8rem; font-weight:600; color:#64748b;">REFERENCE SHEET</span>
              </div>
              
              <h2 style="color:#0f172a; font-size:1.8rem; margin-bottom:1.5rem;">${doc.title}</h2>
              <p style="color:#475569; font-size:0.95rem; margin-bottom:2rem; line-height:1.6;">
                A comprehensive review outlining vector operations, eigenvalues calculation, matrix systems, and proof conditions designed for semester examinations.
              </p>

              <h4 style="color:#4f46e5; border-bottom:1px solid #e2e8f0; padding-bottom:0.5rem; margin-bottom:1rem;">Core Theorems & Forms</h4>
              
              <div style="background:#f8fafc; border-left:4px solid #4f46e5; padding:1rem; margin-bottom:1.5rem; font-family:'Outfit', serif; font-size:1.2rem; display:flex; justify-content:center; align-items:center;">
                <span style="font-style:italic; font-weight:600; color:#4f46e5; margin-right:0.4rem;">det(A - λI)</span> <span style="font-weight:bold; color:#9333ea; margin-right:0.4rem;">=</span> <span>0</span>
              </div>
              <p style="font-size:0.85rem; color:#475569; margin-bottom:1.5rem;">Defines the characteristic polynomial systems used to resolve complex scalar eigenvalues (λ).</p>

              <div style="background:#f8fafc; border-left:4px solid #0891b2; padding:1rem; margin-bottom:1.5rem; font-family:'Outfit', serif; font-size:1.2rem; display:flex; justify-content:center; align-items:center;">
                <span style="font-style:italic; color:#0891b2; margin-right:0.4rem;">Ax</span> <span style="font-weight:bold; color:#9333ea; margin-right:0.4rem;">=</span> <span style="font-style:italic; color:#4f46e5; margin-right:0.2rem;">λ</span><span style="font-style:italic;">x</span>
              </div>
              <p style="font-size:0.85rem; color:#475569;">Proves the transformation matrix properties mapped across non-zero vectors x.</p>
            </div>
            
            <div style="border-top:1px solid #e2e8f0; padding-top:1.5rem; display:flex; justify-content:space-between; font-size:0.8rem; color:#94a3b8; font-weight:600;">
              <span>Copyright &copy; 2026 Ziglag Institute</span>
              <span>Page 1 of 1</span>
            </div>
          </div>
        `;
      }
      
      const modal = document.getElementById("pdf-viewer-modal");
      modal.style.display = "flex";
      
      // Prevent body scrolling
      document.body.style.overflow = "hidden";
    }

    function closePdfModal() {
      document.getElementById("pdf-viewer-modal").style.display = "none";
      document.body.style.overflow = "";
      activePdfDoc = null;
    }

    function triggerDownload() {
      if (activePdfDoc && activePdfDoc.fileUrl) {
        // Create dynamic anchor tag to trigger a download command in the user's browser
        const link = document.createElement("a");
        link.href = activePdfDoc.fileUrl;
        link.download = `${activePdfDoc.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        alert("Download initiated! File compiling into your local Downloads spool directory.");
      }
      closePdfModal();
    }
  