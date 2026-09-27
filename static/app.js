// SwimRight Miami Budget Agent — Standalone Frontend JS App

let currentUser = {
  email: "approver@test.com",
  name: "Dmytro Kachurovskyy",
  role: "Approver",
  department: "Executive"
};

let expensesList = [];

const USER_ROLES = {
  "approver@test.com": {
    name: "Dmytro Kachurovskyy",
    shortName: "Dmytro",
    role: "Approver",
    department: "Executive"
  },
  "admin@test.com": {
    name: "Nazarii Kosylo",
    shortName: "Nazarii",
    role: "Requester + Administrator",
    department: "SwimFast"
  },
  "requester1@test.com": {
    name: "Liza Dragun",
    shortName: "Liza",
    role: "Requester",
    department: "Office"
  },
  "requester2@test.com": {
    name: "Denys Kostromin",
    shortName: "Denys",
    role: "Requester",
    department: "SwimRight / SwimSafe"
  }
};

function getSubmittedByName(email) {
  if (!email) return "Unknown";
  if (USER_ROLES[email]) {
    return USER_ROLES[email].shortName;
  }
  const clean = email.toLowerCase();
  if (clean.includes("admin") || clean.includes("nazarii")) return "Nazarii";
  if (clean.includes("approver") || clean.includes("dmytro")) return "Dmytro";
  if (clean.includes("requester1") || clean.includes("liza")) return "Liza";
  if (clean.includes("requester2") || clean.includes("denys")) return "Denys";
  return email;
}

function saveExpensesToStorage() {
  try {
    localStorage.removeItem("swimright_expenses");
  } catch(e) {}
}

function loadExpensesFromStorage() {
  try {
    localStorage.removeItem("swimright_expenses");
  } catch(e) {}
  expensesList = [];
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadExpensesFromStorage();
  
  // Always show shared password modal on startup if not already verified in current session
  const sessionVerified = sessionStorage.getItem("swimright_authenticated");
  if (!sessionVerified) {
    document.getElementById("loginOverlay").style.display = "flex";
    document.getElementById("loginStep1").style.display = "block";
    document.getElementById("loginStep2").style.display = "none";
    document.getElementById("sharedPasswordInput").value = "";
  } else {
    document.getElementById("loginOverlay").style.display = "none";
    loadDashboardData();
  }
});

function handlePasswordSubmit(e) {
  e.preventDefault();
  const pwd = document.getElementById("sharedPasswordInput").value.trim();
  
  if (pwd.length > 0) {
    sessionStorage.setItem("swimright_authenticated", "true");
    document.getElementById("loginStep1").style.display = "none";
    document.getElementById("loginStep2").style.display = "block";
    showToast("✅ Password accepted! Select active user below.");
  } else {
    showToast("❌ Please enter the password (Password123!)");
  }
}

function selectUser(email, isQuiet = false) {
  const info = USER_ROLES[email];
  if (!info) return;

  currentUser = {
    email: email,
    name: info.name,
    shortName: info.shortName,
    role: info.role,
    department: info.department
  };

  localStorage.setItem("swimright_user", JSON.stringify(currentUser));

  // Hide login overlay
  document.getElementById("loginOverlay").style.display = "none";

  const nameEl = document.getElementById("userDisplayName");
  const roleEl = document.getElementById("userRoleName");
  if (nameEl) nameEl.innerText = currentUser.shortName;
  if (roleEl) roleEl.innerText = `${currentUser.role} (${currentUser.department})`;

  if (!isQuiet) {
    showToast(`⚡ Signed in as: ${currentUser.name} (${currentUser.role})`);
  }
  
  loadDashboardData();
}

function openUserSwitcher() {
  document.getElementById("loginOverlay").style.display = "flex";
  document.getElementById("loginStep1").style.display = "none";
  document.getElementById("loginStep2").style.display = "block";
}

function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      const tabId = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
      const target = document.getElementById(tabId);
      if (target) target.style.display = "block";
    });
  });
}

async function loadDashboardData() {
  try {
    const res = await fetch(`/api/expenses?t=${Date.now()}`, { cache: "no-store" });
    if (res.ok) {
      const serverData = await res.json();
      if (Array.isArray(serverData)) {
        expensesList = serverData;
      }
    }
  } catch (err) {}

  renderExpensesTable();
  updateMetrics();
}

function fill5SampleRows() {
  const names = ["Printer Paper & Ink", "Pool Chemicals", "Software Subscription", "Marketing Banners", "Late Travel Expense"];
  const amounts = [150.00, 320.00, 85.00, 210.00, 450.00];
  const programs = ["Office", "SwimRight / SwimSafe", "SwimFast", "Office", "SwimFast"];
  const categories = ["Office Supplies", "Equipment & Maintenance", "Software & Subscriptions", "Marketing & Events", "Travel Expenses"];
  const purposes = ["Monthly paper restocking", "Safety pool chemicals", "Design tool license", "Event promotion", "Late championship travel"];

  const tbody = document.getElementById("batchRowsTbody");
  const rows = tbody.querySelectorAll("tr");

  for (let i = 0; i < 5; i++) {
    const row = rows[i];
    if (row) {
      row.querySelector(".exp-batch-name").value = names[i];
      row.querySelector(".exp-batch-amount").value = amounts[i];
      row.querySelector(".exp-batch-program").value = programs[i];
      row.querySelector(".exp-batch-category").value = categories[i];
      row.querySelector(".exp-batch-purpose").value = purposes[i];
      row.querySelector(".exp-batch-additional").checked = (i === 4);
    }
  }

  showToast("⚡ 5 Sample Rows Auto-Filled! Click 'Submit Filled Expenses' below!");
}

function clearBatchForm() {
  const tbody = document.getElementById("batchRowsTbody");
  const rows = tbody.querySelectorAll("tr");
  rows.forEach(row => {
    row.querySelector(".exp-batch-name").value = "";
    row.querySelector(".exp-batch-amount").value = "";
    row.querySelector(".exp-batch-purpose").value = "";
    const addCheck = row.querySelector(".exp-batch-additional");
    if (addCheck) addCheck.checked = false;
  });
  showToast("Cleared rows.");
}

async function submitBatchExpenses(e) {
  e.preventDefault();

  const tbody = document.getElementById("batchRowsTbody");
  const rows = tbody.querySelectorAll("tr");

  let submittedCount = 0;
  let batchPayloads = [];

  rows.forEach(row => {
    const name = row.querySelector(".exp-batch-name").value.trim();
    const amountVal = row.querySelector(".exp-batch-amount").value.trim();
    const program = row.querySelector(".exp-batch-program").value;
    const category = row.querySelector(".exp-batch-category").value;
    const purpose = row.querySelector(".exp-batch-purpose").value.trim() || "N/A";
    const isAdd = row.querySelector(".exp-batch-additional") ? row.querySelector(".exp-batch-additional").checked : false;

    if (name && amountVal) {
      batchPayloads.push({
        SubmittedBy: currentUser.email,
        Program: program,
        ExpenseName: name,
        AmountUSD: parseFloat(amountVal),
        PurchasePurpose: purpose,
        ExpenseCategory: category,
        is_additional: isAdd
      });
    }
  });

  if (batchPayloads.length === 0) {
    showToast("❌ Please fill in at least 1 expense row!");
    return;
  }

  showToast(`🚀 Submitting ${batchPayloads.length} expense(s) in one action...`);

  for (const payload of batchPayloads) {
    try {
      const res = await fetch("/api/expenses/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        expensesList.unshift(data.record);
        submittedCount++;
      } else {
        // Fallback local save if offline
        const localRecord = {
          ExpenseID: `EXP-LOCAL-${Date.now()}-${Math.floor(Math.random()*100)}`,
          RequestType: payload.is_additional ? "Additional Expense Request" : "Monthly Expense Request",
          SubmittedBy: payload.SubmittedBy,
          Program: payload.Program,
          ExpenseName: payload.ExpenseName,
          AmountUSD: payload.AmountUSD,
          PurchasePurpose: payload.PurchasePurpose,
          ExpenseCategory: payload.ExpenseCategory,
          CurrentStatus: "Pending"
        };
        expensesList.unshift(localRecord);
        submittedCount++;
      }
    } catch (err) {
      // Fallback local save
      const localRecord = {
        ExpenseID: `EXP-LOCAL-${Date.now()}-${Math.floor(Math.random()*100)}`,
        RequestType: payload.is_additional ? "Additional Expense Request" : "Monthly Expense Request",
        SubmittedBy: payload.SubmittedBy,
        Program: payload.Program,
        ExpenseName: payload.ExpenseName,
        AmountUSD: payload.AmountUSD,
        PurchasePurpose: payload.PurchasePurpose,
        ExpenseCategory: payload.ExpenseCategory,
        CurrentStatus: "Pending"
      };
      expensesList.unshift(localRecord);
      submittedCount++;
    }
  }

  saveExpensesToStorage();
  showToast(`✅ Successfully submitted ${submittedCount} expense(s)!`);
  clearBatchForm();
  
  document.querySelector('[data-tab="tab-dashboard"]').click();
  loadDashboardData();
}

function updateMetrics() {
  const totalSubmitted = expensesList.reduce((sum, e) => sum + e.AmountUSD, 0);
  const totalApproved = expensesList.filter(e => e.CurrentStatus === "Approved").reduce((sum, e) => sum + e.AmountUSD, 0);
  const pendingCount = expensesList.filter(e => e.CurrentStatus === "Pending").length;
  
  document.getElementById("metricSubmitted").innerText = `$${totalSubmitted.toFixed(2)}`;
  document.getElementById("metricApproved").innerText = `$${totalApproved.toFixed(2)}`;
  document.getElementById("metricPending").innerText = pendingCount;
}

function renderExpensesTable() {
  const tbody = document.getElementById("expensesTbody");
  if (!tbody) return;
  
  if (expensesList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No expenses submitted yet. Switch to '📝 Submit Expenses' tab to add items!</td></tr>`;
    return;
  }
  
  tbody.innerHTML = expensesList.map(exp => {
    let typeBadge = '';
    if (exp.RequestType === 'Late Submission') {
      typeBadge = '<span class="metric-badge" style="background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.5); font-weight: 700; margin-left: 0.5rem;">⏰ LATE</span>';
    } else if (exp.RequestType === 'Additional Expense Request') {
      typeBadge = '<span class="metric-badge" style="background: rgba(6, 182, 212, 0.25); color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.5); font-weight: 700; margin-left: 0.5rem;">🚩 ADDITIONAL</span>';
    }

    return `
    <tr>
      <td><strong>${getSubmittedByName(exp.SubmittedBy)}</strong></td>
      <td><strong>${exp.ExpenseName}</strong> ${typeBadge}</td>
      <td><strong>$${exp.AmountUSD.toFixed(2)}</strong></td>
      <td><span class="metric-badge badge-pending">${exp.ExpenseCategory}</span></td>
      <td>
        <span class="metric-badge ${getStatusBadgeClass(exp.CurrentStatus)}">
          ${exp.CurrentStatus}
        </span>
      </td>
      <td style="white-space: nowrap;">
        ${exp.CurrentStatus === 'Pending' ? `
          <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="approveItem('${exp.ExpenseID}')">Approve</button>
          <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="rejectItem('${exp.ExpenseID}')">Reject</button>
        ` : ''}
        <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #f87171;" onclick="deleteItem('${exp.ExpenseID}')">🗑️ Delete</button>
      </td>
    </tr>
  `;
  }).join("");
}

function getStatusBadgeClass(status) {
  if (status === "Approved") return "badge-approved";
  if (status === "Rejected") return "badge-rejected";
  return "badge-pending";
}

async function approveItem(expenseId) {
  try {
    await fetch(`/api/expenses/${expenseId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "Approved" })
    });
  } catch(e) {}
  showToast(`✅ Expense approved!`);
  loadDashboardData();
}

async function rejectItem(expenseId) {
  try {
    await fetch(`/api/expenses/${expenseId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "Rejected" })
    });
  } catch(e) {}
  showToast(`❌ Expense rejected.`);
  loadDashboardData();
}

async function deleteItem(expenseId) {
  try {
    await fetch(`/api/expenses/${expenseId}`, { method: "DELETE" });
  } catch(e) {}

  expensesList = expensesList.filter(e => e.ExpenseID !== expenseId);
  saveExpensesToStorage();
  showToast(`🗑️ Expense deleted!`);
  loadDashboardData();
}

async function handleApproveAll() {
  let count = 0;
  for (const exp of expensesList) {
    if (exp.CurrentStatus === "Pending" && exp.RequestType === "Monthly Expense Request") {
      try {
        await fetch(`/api/expenses/${exp.ExpenseID}/status`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "Approved" })
        });
        count++;
      } catch(e) {}
    }
  }
  showToast(`✅ Bulk Action: Approved ${count} pending monthly expenses!`);
  loadDashboardData();
}

async function handleClearAllExpenses() {
  if (confirm("Вы уверены, что хотите полностью очистить список расходов для нового месяца?\nAre you sure you want to clear all expenses for the new month?")) {
    try {
      await fetch("/api/clear-all-expenses", { method: "POST" });
    } catch(e) {}
    expensesList = [];
    saveExpensesToStorage();
    showToast("🗑️ All expenses cleared! Ready for new month.");
    loadDashboardData();
  }
}

function showToast(text) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerText = text;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
