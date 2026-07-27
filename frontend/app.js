// ============================================================
// StudyFinder frontend
// Vanilla JS single-page app that talks to the FastAPI backend.
// ============================================================

const STORAGE_KEY = "studyfinder_user";

const state = {
  user: null,          // { id, display_name, email, major, school_year }
  currentDiscussionGroup: null, // { id, group_name, course_code }
  discussionPosts: [],
  selectedPostId: null,
  editingSessionId: null,
};

// ----------------------- generic helpers -----------------------

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let body = null;
  const text = await response.text();

  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    const detail = body && body.detail ? body.detail : "Something went wrong.";
    throw new Error(detail);
  }

  return body;
}

function showToast(message, type = "success") {
  const toast = document.getElementById("notification-toast");
  toast.textContent = message;
  toast.className = `notification-toast ${type}`;
  toast.classList.remove("hidden");

  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    toast.classList.add("hidden");
  }, 3200);
}

function setMessage(elementId, message, type = "error") {
  const el = document.getElementById(elementId);
  el.textContent = message || "";
  el.className = `form-message ${message ? type : ""}`;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function initials(name) {
  if (!name) return "?";
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function formatRelativeTime(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return formatDate(isoString);
}

function dayBadge(isoString) {
  const target = new Date(isoString);
  const now = new Date();
  const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round(
    (startOfDay(target) - startOfDay(now)) / (1000 * 60 * 60 * 24)
  );

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays > 1 && diffDays < 7) {
    return target.toLocaleDateString(undefined, { weekday: "long" });
  }
  return formatDate(isoString);
}

function notificationIcon(message) {
  const lower = message.toLowerCase();
  if (lower.includes("session")) return "🗓️";
  if (lower.includes("discussion") || lower.includes("repl")) return "💬";
  if (lower.includes("joined") || lower.includes("member")) return "👥";
  return "🔔";
}

function greetingWord() {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

// ----------------------- auth -----------------------

function persistUser(user) {
  state.user = user;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

function loadPersistedUser() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function logout() {
  state.user = null;
  localStorage.removeItem(STORAGE_KEY);
  document.getElementById("application-view").classList.add("hidden");
  document.getElementById("authentication-view").classList.remove("hidden");
  document.getElementById("login-form").reset();
  document.getElementById("edit-profile-dialog").close();
}

async function handleLogin(event) {
  event.preventDefault();
  setMessage("login-message", "");

  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    persistUser(result.user);
    enterApp();
  } catch (error) {
    setMessage("login-message", error.message, "error");
  }
}

async function handleRegister(event) {
  event.preventDefault();
  setMessage("register-message", "");

  const display_name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const major = document.getElementById("register-major").value.trim();
  const password = document.getElementById("register-password").value;

  try {
    const result = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        display_name,
        email,
        password,
        major: major || null,
      }),
    });
    persistUser(result.user);
    enterApp();
  } catch (error) {
    setMessage("register-message", error.message, "error");
  }
}

function setupAuthSwitcher() {
  const switchButton = document.getElementById("authentication-switch-button");
  const switchText = document.getElementById("switch-text");
  const title = document.getElementById("authentication-title");
  const subtitle = document.getElementById("authentication-subtitle");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  let showingLogin = true;

  switchButton.addEventListener("click", () => {
    showingLogin = !showingLogin;
    loginForm.classList.toggle("hidden", !showingLogin);
    registerForm.classList.toggle("hidden", showingLogin);
    title.textContent = showingLogin ? "Welcome back" : "Create your account";
    subtitle.textContent = showingLogin
      ? "Sign in to continue to StudyFinder"
      : "Join StudyFinder to find your people";
    switchText.textContent = showingLogin
      ? "New to StudyFinder?"
      : "Already have an account?";
    switchButton.textContent = showingLogin ? "Create an account" : "Sign in";
    setMessage("login-message", "");
    setMessage("register-message", "");
  });
}

// ----------------------- navigation -----------------------

function setupNavigation() {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });

  document.querySelectorAll("[data-view-link]").forEach((el) => {
    el.addEventListener("click", () => showView(el.dataset.viewLink));
  });

  document.getElementById("bell-button").addEventListener("click", () => {
    showView("notifications");
  });

  document.getElementById("topbar-user-button").addEventListener("click", () => {
    showView("profile");
  });
}

function showView(viewName) {
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.add("hidden");
  });
  document.getElementById(`view-${viewName}`).classList.remove("hidden");

  document.querySelectorAll(".nav-item").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === viewName);
  });

  if (viewName === "dashboard") loadDashboard();
  if (viewName === "discover-groups") loadDiscoverGroups();
  if (viewName === "my-groups") loadMyGroups();
  if (viewName === "sessions") loadSessionsPage();
  if (viewName === "discussions") loadDiscussionsPicker();
  if (viewName === "notifications") loadNotificationsPage();
  if (viewName === "profile") loadProfilePage();
}

function updateTopbar() {
  document.getElementById("topbar-avatar").textContent = initials(
    state.user.display_name
  );
  document.getElementById("topbar-user-name").textContent =
    state.user.display_name;
}

async function enterApp() {
  document.getElementById("authentication-view").classList.add("hidden");
  document.getElementById("application-view").classList.remove("hidden");
  updateTopbar();
  showView("dashboard");
}

function setUnreadIndicators(unreadCount) {
  const show = unreadCount > 0;
  document.getElementById("sidebar-unread-dot").classList.toggle("hidden", !show);
  document.getElementById("bell-unread-dot").classList.toggle("hidden", !show);
}

// ----------------------- dashboard -----------------------

async function loadDashboard() {
  try {
    const data = await api(`/dashboard/${state.user.id}`);
    const firstName = state.user.display_name.split(" ")[0];

    document.getElementById(
      "greeting-text"
    ).textContent = `Good ${greetingWord()}, ${firstName} 👋`;
    document.getElementById("greeting-subtext").textContent =
      `You have ${data.stats.upcoming_sessions} study session${
        data.stats.upcoming_sessions === 1 ? "" : "s"
      } coming up this week.`;

    document.getElementById("stat-joined-groups").textContent =
      data.stats.joined_groups;
    document.getElementById("stat-upcoming-sessions").textContent =
      data.stats.upcoming_sessions;
    document.getElementById("stat-unread-updates").textContent =
      data.stats.unread_updates;
    document.getElementById("stat-discussion-posts").textContent =
      data.stats.discussion_posts;

    setUnreadIndicators(data.stats.unread_updates);

    renderDashboardSessions(data.upcoming_sessions);
    renderRecentlyJoined(data.recently_joined);
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderDashboardSessions(sessions) {
  const container = document.getElementById("dashboard-upcoming-sessions");

  if (!sessions || sessions.length === 0) {
    container.innerHTML = `<p class="muted">No upcoming sessions yet.</p>`;
    return;
  }

  container.innerHTML = sessions
    .map(
      (session) => `
      <div class="session-card" data-view-session="${session.id}" style="cursor:pointer">
        <div class="session-card-left">
          <span class="session-icon">🗓️</span>
          <div>
            <h3>${escapeHtml(session.title)}</h3>
            <p class="session-meta-line">${escapeHtml(session.course_code)} · ${escapeHtml(
        session.group_name
      )}</p>
            <p class="session-detail-line">
              <span>🕐 ${formatDate(session.scheduled_at)}, ${formatTime(
        session.scheduled_at
      )}</span>
              ${session.location ? `<span>📍 ${escapeHtml(session.location)}</span>` : ""}
            </p>
          </div>
        </div>
        <span class="session-day-badge">${dayBadge(session.scheduled_at)}</span>
      </div>
    `
    )
    .join("");

  container.querySelectorAll("[data-view-session]").forEach((el) => {
    el.addEventListener("click", () =>
      openSessionViewDialog(Number(el.dataset.viewSession))
    );
  });
}

function renderRecentlyJoined(groups) {
  const container = document.getElementById("recently-joined-list");

  if (!groups || groups.length === 0) {
    container.innerHTML = `<p class="muted">No groups yet.</p>`;
    return;
  }

  container.innerHTML = groups
    .map(
      (group) => `
      <div class="recently-joined-item">
        <div class="info">
          <span class="avatar-circle avatar-small">${escapeHtml(
            group.group_name.charAt(0)
          )}</span>
          <div>
            <h4>${escapeHtml(group.group_name)}</h4>
            <p>${escapeHtml(group.course_code)}</p>
          </div>
        </div>
      </div>
    `
    )
    .join("");
}

// ----------------------- discover groups -----------------------

function setupDiscoverGroups() {
  document.getElementById("search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const query = document.getElementById("search-input").value.trim();
    performGroupSearch(query);
  });
}

async function loadDiscoverGroups() {
  document.getElementById("discover-groups-heading").textContent =
    "Recommended for you";
  document.getElementById("search-input").value = "";
  await performGroupSearch("");
}

async function performGroupSearch(query) {
  const listEl = document.getElementById("discover-groups-list");
  const countEl = document.getElementById("discover-groups-count");
  listEl.innerHTML = `<p class="muted">Loading groups…</p>`;

  try {
    const groups = await api(
      `/study-groups/${query ? `?course_code=${encodeURIComponent(query)}` : ""}`
    );

    document.getElementById("discover-groups-heading").textContent = query
      ? `Results for "${query}"`
      : "Recommended for you";
    countEl.textContent = `${groups.length} group${groups.length === 1 ? "" : "s"} found`;

    if (groups.length === 0) {
      listEl.innerHTML = `<p class="muted">No study groups match that search.</p>`;
      return;
    }

    const withCounts = await Promise.all(
      groups.map(async (group) => {
        try {
          const members = await api(`/study-groups/${group.id}/members`);
          return {
            ...group,
            member_count: members.length,
            is_member: members.some((m) => m.user_id === state.user.id),
          };
        } catch {
          return { ...group, member_count: 0, is_member: false };
        }
      })
    );

    listEl.innerHTML = withCounts
      .map((group) => {
        const isFull = group.member_count >= group.max_members;
        const isCreator = group.creator_user_id === state.user.id;
        const statusBadge = isFull
          ? `<span class="badge badge-gray">Full</span>`
          : `<span class="badge badge-green">Open</span>`;

        let actionButton;
        if (isCreator) {
          actionButton = `<span class="badge badge-purple">Creator</span>`;
        } else if (group.is_member) {
          actionButton = `<span class="badge badge-gray">Member</span>`;
        } else if (isFull) {
          actionButton = `<button class="btn-outline" disabled>Full</button>`;
        } else {
          actionButton = `<button class="btn-primary-small" data-join="${group.id}">Join</button>`;
        }

        return `
          <div class="discover-group-card">
            <div class="info">
              <div class="group-title-row">
                <h3>${escapeHtml(group.group_name)}</h3>
                ${statusBadge}
              </div>
              <span class="course-code">${escapeHtml(group.course_code)}</span>
              <p class="description">${escapeHtml(group.description || "")}</p>
              <p class="member-line">${group.member_count}/${group.max_members} members</p>
            </div>
            <div class="actions">
              ${actionButton}
              <button class="btn-outline" data-view-group="${group.id}">View group</button>
            </div>
          </div>
        `;
      })
      .join("");

    listEl.querySelectorAll("[data-join]").forEach((button) => {
      button.addEventListener("click", () => joinGroup(Number(button.dataset.join)));
    });

    listEl.querySelectorAll("[data-view-group]").forEach((button) => {
      button.addEventListener("click", () =>
        openGroupViewDialog(Number(button.dataset.viewGroup))
      );
    });
  } catch (error) {
    listEl.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

async function joinGroup(groupId) {
  try {
    await api(`/study-groups/${groupId}/members/${state.user.id}`, {
      method: "POST",
    });
    showToast("You joined the study group.");
    const active = document.querySelector(".nav-item.active").dataset.view;
    showView(active);
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function leaveGroup(groupId) {
  try {
    await api(`/study-groups/${groupId}/members/${state.user.id}`, {
      method: "DELETE",
    });
    showToast("You left the study group.");
    const active = document.querySelector(".nav-item.active").dataset.view;
    showView(active);
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function openGroupViewDialog(groupId) {
  const dialog = document.getElementById("session-view-dialog");
  const content = document.getElementById("session-view-content");
  content.innerHTML = `<p class="muted">Loading…</p>`;
  dialog.showModal();

  try {
    const [group, members] = await Promise.all([
      api(`/study-groups/${groupId}`),
      api(`/study-groups/${groupId}/members`),
    ]);

    content.innerHTML = `
      <h2>${escapeHtml(group.group_name)}</h2>
      <p class="muted">${escapeHtml(group.course_code)} · ${members.length}/${
      group.max_members
    } members · ${escapeHtml(group.status)}</p>
      <p>${escapeHtml(group.description || "")}</p>
      <h3 style="font-size:14px;margin-top:20px;">Members</h3>
      ${
        members
          .map(
            (m) =>
              `<div class="profile-info-row"><span>${escapeHtml(m.display_name)}</span></div>`
          )
          .join("") || `<p class="muted">No members yet.</p>`
      }
    `;
  } catch (error) {
    content.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

// ----------------------- my groups -----------------------

async function loadMyGroups() {
  const createdEl = document.getElementById("created-groups-grid");
  const joinedEl = document.getElementById("joined-groups-list");

  try {
    const groups = await api(`/users/${state.user.id}/study-groups`);
    const created = groups.filter((g) => g.creator_user_id === state.user.id);
    const joined = groups.filter((g) => g.creator_user_id !== state.user.id);

    createdEl.innerHTML = created.length
      ? created
          .map(
            (group) => `
        <div class="created-group-card">
          <div class="top-row">
            <span class="badge badge-purple">Creator</span>
          </div>
          <h3>${escapeHtml(group.group_name)}</h3>
          <span class="course-code">${escapeHtml(group.course_code)}</span>
          <p class="member-line">${group.member_count} members</p>
          <button class="btn-outline" data-manage-group="${group.id}">✎ Manage group</button>
        </div>
      `
          )
          .join("")
      : `<p class="muted">You haven't created any groups yet.</p>`;

    joinedEl.innerHTML = joined.length
      ? joined
          .map(
            (group) => `
        <div class="joined-group-row">
          <div class="info">
            <span class="avatar-circle avatar-medium">${escapeHtml(
              group.group_name.charAt(0)
            )}</span>
            <div>
              <h3>${escapeHtml(group.group_name)}</h3>
              <p>${escapeHtml(group.course_code)} · ${group.member_count} members</p>
            </div>
          </div>
          <div class="actions">
            <button class="btn-outline" data-view-group="${group.id}">Open</button>
            <button class="btn-danger" data-leave-group="${group.id}">Leave group</button>
          </div>
        </div>
      `
          )
          .join("")
      : `<p class="muted">You haven't joined any groups yet.</p>`;

    createdEl.querySelectorAll("[data-manage-group]").forEach((button) => {
      button.addEventListener("click", () =>
        openGroupViewDialog(Number(button.dataset.manageGroup))
      );
    });

    joinedEl.querySelectorAll("[data-view-group]").forEach((button) => {
      button.addEventListener("click", () =>
        openGroupViewDialog(Number(button.dataset.viewGroup))
      );
    });

    joinedEl.querySelectorAll("[data-leave-group]").forEach((button) => {
      button.addEventListener("click", () =>
        leaveGroup(Number(button.dataset.leaveGroup))
      );
    });
  } catch (error) {
    showToast(error.message, "error");
  }
}

function setupCreateGroup() {
  const dialog = document.getElementById("create-group-dialog");

  document.getElementById("open-create-group-button").addEventListener("click", () => {
    document.getElementById("create-group-form").reset();
    document.getElementById("max-members").value = 10;
    setMessage("create-group-message", "");
    dialog.showModal();
  });

  document
    .getElementById("create-group-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      setMessage("create-group-message", "");

      const group_name = document.getElementById("group-name").value.trim();
      const course_code = document.getElementById("course-code").value.trim();
      const description = document.getElementById("group-description").value.trim();
      const max_members = Number(document.getElementById("max-members").value);
      const status = document.getElementById("group-status").value;

      try {
        await api("/study-groups/", {
          method: "POST",
          body: JSON.stringify({
            group_name,
            course_code,
            description,
            creator_user_id: state.user.id,
            status,
            max_members,
          }),
        });
        showToast("Study group created.");
        dialog.close();
        loadMyGroups();
      } catch (error) {
        setMessage("create-group-message", error.message, "error");
      }
    });
}

// ----------------------- sessions -----------------------

async function loadSessionsPage() {
  const upcomingEl = document.getElementById("upcoming-sessions-list");
  const pastEl = document.getElementById("past-sessions-list");
  upcomingEl.innerHTML = `<p class="muted">Loading…</p>`;
  pastEl.innerHTML = "";

  try {
    const groups = await api(`/users/${state.user.id}/study-groups`);

    const sessionsByGroup = await Promise.all(
      groups.map(async (group) => {
        const sessions = await api(`/study-groups/${group.id}/sessions`);
        return sessions.map((s) => ({
          ...s,
          group_name: group.group_name,
          course_code: group.course_code,
          can_manage: group.creator_user_id === state.user.id,
        }));
      })
    );

    const allSessions = sessionsByGroup.flat();
    const now = new Date();
    const upcoming = allSessions
      .filter((s) => new Date(s.scheduled_at) >= now)
      .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
    const past = allSessions
      .filter((s) => new Date(s.scheduled_at) < now)
      .sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at));

    renderSessionsList(upcomingEl, upcoming, true);
    renderSessionsList(pastEl, past, false);
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderSessionsList(container, sessions, isUpcoming) {
  if (!sessions || sessions.length === 0) {
    container.innerHTML = `<p class="muted">No ${
      isUpcoming ? "upcoming" : "past"
    } sessions yet.</p>`;
    return;
  }

  container.innerHTML = sessions
    .map((session) => {
      let actions;
      if (isUpcoming && session.can_manage) {
        actions = `
          <button class="btn-outline" data-edit-session="${session.id}">Edit</button>
          <button class="btn-danger" data-cancel-session="${session.id}">Cancel</button>
        `;
      } else {
        actions = `<button class="btn-outline" data-view-session="${session.id}">View</button>`;
      }

      return `
        <div class="session-card">
          <div class="session-card-left">
            <span class="session-icon">🗓️</span>
            <div>
              <h3>${escapeHtml(session.title)}</h3>
              <p class="session-meta-line">${escapeHtml(session.group_name)}</p>
              <p class="session-detail-line">
                <span>🕐 ${formatDate(session.scheduled_at)} · ${formatTime(
        session.scheduled_at
      )} · ${session.duration_minutes} min</span>
                ${session.location ? `<span>📍 ${escapeHtml(session.location)}</span>` : ""}
              </p>
            </div>
          </div>
          <div class="session-card-actions">${actions}</div>
        </div>
      `;
    })
    .join("");

  container.querySelectorAll("[data-view-session]").forEach((el) => {
    el.addEventListener("click", () =>
      openSessionViewDialog(Number(el.dataset.viewSession))
    );
  });

  container.querySelectorAll("[data-edit-session]").forEach((el) => {
    el.addEventListener("click", () =>
      openSessionDialog({ sessionId: Number(el.dataset.editSession) })
    );
  });

  container.querySelectorAll("[data-cancel-session]").forEach((el) => {
    el.addEventListener("click", () => cancelSession(Number(el.dataset.cancelSession)));
  });
}

async function cancelSession(sessionId) {
  try {
    await api(`/sessions/${sessionId}`, { method: "DELETE" });
    showToast("Session canceled.");
    const active = document.querySelector(".nav-item.active").dataset.view;
    showView(active);
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function openSessionViewDialog(sessionId) {
  const dialog = document.getElementById("session-view-dialog");
  const content = document.getElementById("session-view-content");
  content.innerHTML = `<p class="muted">Loading…</p>`;
  dialog.showModal();

  try {
    const session = await api(`/sessions/${sessionId}`);
    const group = await api(`/study-groups/${session.group_id}`);

    content.innerHTML = `
      <h2>${escapeHtml(session.title)}</h2>
      <p class="muted">${escapeHtml(group.course_code)} · ${escapeHtml(group.group_name)}</p>
      <div class="profile-info-row"><span class="muted">Date</span><span>${formatDate(
        session.scheduled_at
      )}</span></div>
      <div class="profile-info-row"><span class="muted">Time</span><span>${formatTime(
        session.scheduled_at
      )}</span></div>
      <div class="profile-info-row"><span class="muted">Duration</span><span>${
        session.duration_minutes
      } min</span></div>
      <div class="profile-info-row"><span class="muted">Location</span><span>${escapeHtml(
        session.location || "—"
      )}</span></div>
      ${
        session.meeting_link
          ? `<div class="profile-info-row"><span class="muted">Meeting link</span><span>${escapeHtml(
              session.meeting_link
            )}</span></div>`
          : ""
      }
    `;
  } catch (error) {
    content.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

async function openSessionDialog({ sessionId = null, defaultGroupId = null } = {}) {
  const dialog = document.getElementById("session-dialog");
  const form = document.getElementById("session-form");
  const groupSelect = document.getElementById("session-group-select");
  const groupLabel = document.getElementById("session-group-label");

  form.reset();
  setMessage("session-message", "");
  state.editingSessionId = sessionId;

  let groups;
  try {
    groups = await api(`/users/${state.user.id}/study-groups`);
  } catch (error) {
    showToast(error.message, "error");
    return;
  }

  const manageable = groups.filter((g) => g.creator_user_id === state.user.id);

  groupSelect.innerHTML = manageable
    .map(
      (g) =>
        `<option value="${g.id}">${escapeHtml(g.group_name)} (${escapeHtml(
          g.course_code
        )})</option>`
    )
    .join("");

  if (sessionId) {
    document.getElementById("session-dialog-title").textContent = "Edit Session";
    groupLabel.classList.add("hidden");
    groupSelect.classList.add("hidden");
    groupSelect.required = false;

    try {
      const session = await api(`/sessions/${sessionId}`);
      document.getElementById("session-title").value = session.title;
      document.getElementById("session-location").value = session.location || "";
      document.getElementById("session-meeting-link").value =
        session.meeting_link || "";
      document.getElementById("session-duration").value = session.duration_minutes;

      const localDate = new Date(session.scheduled_at);
      const tzOffset = localDate.getTimezoneOffset() * 60000;
      document.getElementById("session-time").value = new Date(localDate - tzOffset)
        .toISOString()
        .slice(0, 16);
    } catch (error) {
      showToast(error.message, "error");
      return;
    }
  } else {
    document.getElementById("session-dialog-title").textContent = "Create Session";
    groupLabel.classList.remove("hidden");
    groupSelect.classList.remove("hidden");
    groupSelect.required = true;
    if (defaultGroupId) groupSelect.value = defaultGroupId;
  }

  dialog.showModal();
}

function setupSessionDialog() {
  document.getElementById("open-create-session-button").addEventListener("click", () => {
    openSessionDialog({});
  });

  document.getElementById("session-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("session-message", "");

    const title = document.getElementById("session-title").value.trim();
    const location = document.getElementById("session-location").value.trim();
    const meeting_link = document.getElementById("session-meeting-link").value.trim();
    const scheduled_at = document.getElementById("session-time").value;
    const duration_minutes = Number(document.getElementById("session-duration").value);

    const payload = {
      title,
      location: location || null,
      meeting_link: meeting_link || null,
      scheduled_at,
      duration_minutes,
    };

    try {
      if (state.editingSessionId) {
        await api(`/sessions/${state.editingSessionId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        showToast("Session updated.");
      } else {
        const groupId = document.getElementById("session-group-select").value;
        if (!groupId) {
          setMessage("session-message", "Choose a group first.", "error");
          return;
        }
        await api(`/study-groups/${groupId}/sessions`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        showToast("Session scheduled.");
      }

      document.getElementById("session-dialog").close();
      const active = document.querySelector(".nav-item.active").dataset.view;
      showView(active);
    } catch (error) {
      setMessage("session-message", error.message, "error");
    }
  });
}

// ----------------------- discussions -----------------------

async function loadDiscussionsPicker() {
  document.getElementById("discussions-picker").classList.remove("hidden");
  document.getElementById("discussions-thread-view").classList.add("hidden");

  const container = document.getElementById("discussions-group-list");
  container.innerHTML = `<p class="muted">Loading…</p>`;

  try {
    const groups = await api(`/users/${state.user.id}/study-groups`);

    if (groups.length === 0) {
      container.innerHTML = `<p class="muted">Join a group to start a discussion.</p>`;
      return;
    }

    container.innerHTML = groups
      .map(
        (group) => `
        <div class="discussions-group-row" data-open-discussion="${group.id}" data-group-name="${escapeHtml(
          group.group_name
        )}" data-course-code="${escapeHtml(group.course_code)}">
          <div class="info">
            <span class="avatar-circle avatar-medium">${escapeHtml(
              group.group_name.charAt(0)
            )}</span>
            <div>
              <h3>${escapeHtml(group.group_name)}</h3>
              <p>${escapeHtml(group.course_code)}</p>
            </div>
          </div>
          <span class="link-text">Open →</span>
        </div>
      `
      )
      .join("");

    container.querySelectorAll("[data-open-discussion]").forEach((el) => {
      el.addEventListener("click", () =>
        openDiscussionThread(
          Number(el.dataset.openDiscussion),
          el.dataset.groupName,
          el.dataset.courseCode
        )
      );
    });
  } catch (error) {
    container.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

async function openDiscussionThread(groupId, groupName, courseCode) {
  state.currentDiscussionGroup = {
    id: groupId,
    group_name: groupName,
    course_code: courseCode,
  };
  state.selectedPostId = null;

  document.getElementById("discussions-picker").classList.add("hidden");
  document.getElementById("discussions-thread-view").classList.remove("hidden");
  document.getElementById("discussions-group-title").textContent = "Group Discussion";
  document.getElementById("discussions-group-subtitle").textContent = groupName;

  await refreshDiscussionPosts();
}

async function refreshDiscussionPosts() {
  const listEl = document.getElementById("discussion-posts-list");
  listEl.innerHTML = `<p class="muted">Loading…</p>`;

  try {
    const posts = await api(`/study-groups/${state.currentDiscussionGroup.id}/posts`);
    state.discussionPosts = posts;
    renderDiscussionPostsList();

    if (state.selectedPostId) {
      renderSelectedThread(state.selectedPostId);
    } else {
      document.getElementById("selected-thread-content").innerHTML =
        `<p class="muted">Select a post to see replies.</p>`;
    }
  } catch (error) {
    listEl.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

function renderDiscussionPostsList() {
  const listEl = document.getElementById("discussion-posts-list");
  const topLevel = state.discussionPosts
    .filter((p) => !p.parent_post_id)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  if (topLevel.length === 0) {
    listEl.innerHTML = `<p class="muted">No discussion posts yet.</p>`;
    return;
  }

  listEl.innerHTML = topLevel
    .map((post) => {
      const replyCount = state.discussionPosts.filter(
        (p) => p.parent_post_id === post.id
      ).length;
      const selected = post.id === state.selectedPostId ? "selected" : "";

      return `
        <div class="discussion-post-card ${selected}" data-post-id="${post.id}">
          <div class="post-author-row">
            <span class="avatar-circle avatar-small">${initials(post.author_name)}</span>
            <span class="name">${escapeHtml(post.author_name)}</span>
            <span class="time">${formatRelativeTime(post.created_at)}</span>
          </div>
          <h4>${escapeHtml(post.title || "")}</h4>
          <p class="content">${escapeHtml(post.content)}</p>
          <div class="post-footer-row">
            <span class="link-text">${replyCount} repl${replyCount === 1 ? "y" : "ies"}</span>
            <span class="link-text">Reply</span>
          </div>
        </div>
      `;
    })
    .join("");

  listEl.querySelectorAll("[data-post-id]").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedPostId = Number(el.dataset.postId);
      renderDiscussionPostsList();
      renderSelectedThread(state.selectedPostId);
    });
  });
}

function renderSelectedThread(postId) {
  const post = state.discussionPosts.find((p) => p.id === postId);
  const container = document.getElementById("selected-thread-content");

  if (!post) {
    container.innerHTML = `<p class="muted">Select a post to see replies.</p>`;
    return;
  }

  const replies = state.discussionPosts
    .filter((p) => p.parent_post_id === postId)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  container.innerHTML = `
    <h3 style="margin-top:0;font-size:16px;">${escapeHtml(post.title || "")}</h3>
    <p class="muted" style="font-size:13px;margin-bottom:18px;">${escapeHtml(post.content)}</p>
    <h4 style="font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;">Replies</h4>
    <div id="replies-list">
      ${
        replies
          .map(
            (reply) => `
        <div class="reply-item">
          <span class="avatar-circle avatar-small">${initials(reply.author_name)}</span>
          <div>
            <div class="name">${escapeHtml(reply.author_name)}</div>
            <p>${escapeHtml(reply.content)}</p>
          </div>
        </div>
      `
          )
          .join("") || `<p class="muted">No replies yet.</p>`
      }
    </div>
    <form class="reply-form" id="reply-form">
      <textarea id="reply-content" placeholder="Write a reply..." required></textarea>
      <button class="main-button" type="submit">Post reply</button>
    </form>
  `;

  document.getElementById("reply-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = document.getElementById("reply-content").value.trim();

    try {
      await api(`/study-groups/${state.currentDiscussionGroup.id}/posts`, {
        method: "POST",
        body: JSON.stringify({
          content,
          user_id: state.user.id,
          parent_post_id: postId,
        }),
      });
      showToast("Reply posted.");
      await refreshDiscussionPosts();
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

function setupDiscussions() {
  document.getElementById("discussions-back-button").addEventListener("click", () => {
    loadDiscussionsPicker();
  });

  document.getElementById("open-create-post-button").addEventListener("click", () => {
    document.getElementById("create-post-form").reset();
    setMessage("create-post-message", "");
    document.getElementById("create-post-dialog").showModal();
  });

  document
    .getElementById("create-post-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      setMessage("create-post-message", "");

      const title = document.getElementById("post-title").value.trim();
      const content = document.getElementById("post-content").value.trim();

      try {
        await api(`/study-groups/${state.currentDiscussionGroup.id}/posts`, {
          method: "POST",
          body: JSON.stringify({ title, content, user_id: state.user.id }),
        });
        showToast("Posted to the group.");
        document.getElementById("create-post-dialog").close();
        await refreshDiscussionPosts();
      } catch (error) {
        setMessage("create-post-message", error.message, "error");
      }
    });
}

// ----------------------- notifications -----------------------

async function loadNotificationsPage() {
  const container = document.getElementById("notifications-list");
  container.innerHTML = `<p class="muted">Loading…</p>`;

  try {
    const notificationsData = await api(`/notifications/${state.user.id}`);

    if (notificationsData.length === 0) {
      container.innerHTML = `<p class="muted">No notifications yet.</p>`;
      return;
    }

    container.innerHTML = notificationsData
      .map((n) => {
        return `
        <div class="notification-card ${n.is_read ? "" : "unread"}" data-notification-id="${n.id}">
          <span class="notification-icon">${notificationIcon(n.message)}</span>
          <div>
            <p class="body">${escapeHtml(n.message)}</p>
            <span class="time">${formatRelativeTime(n.created_at)}</span>
          </div>
          ${n.is_read ? "" : '<span class="unread-dot"></span>'}
        </div>
      `;
      })
      .join("");

    container.querySelectorAll("[data-notification-id]").forEach((el) => {
      el.addEventListener("click", async () => {
        const id = Number(el.dataset.notificationId);
        try {
          await api(`/notifications/${id}/read`, { method: "PUT" });
          loadNotificationsPage();
          refreshUnreadBadge();
        } catch (error) {
          showToast(error.message, "error");
        }
      });
    });
  } catch (error) {
    container.innerHTML = `<p class="form-message error">${escapeHtml(error.message)}</p>`;
  }
}

async function refreshUnreadBadge() {
  try {
    const data = await api(`/dashboard/${state.user.id}`);
    setUnreadIndicators(data.stats.unread_updates);
  } catch {
    // non-critical, ignore
  }
}

function setupNotifications() {
  document
    .getElementById("mark-all-read-button")
    .addEventListener("click", async () => {
      try {
        await api(`/notifications/${state.user.id}/read-all`, { method: "POST" });
        showToast("All notifications marked as read.");
        loadNotificationsPage();
        setUnreadIndicators(0);
      } catch (error) {
        showToast(error.message, "error");
      }
    });
}

// ----------------------- profile -----------------------

async function loadProfilePage() {
  try {
    const [profileData, groups] = await Promise.all([
      api(`/users/${state.user.id}/profile`),
      api(`/users/${state.user.id}/study-groups`),
    ]);

    const user = profileData.user;

    document.getElementById("profile-avatar").textContent = initials(user.display_name);
    document.getElementById("profile-name").textContent = user.display_name;
    document.getElementById("profile-email").textContent = user.email;
    document.getElementById("profile-major-badge").textContent =
      user.major || "Undeclared";
    document.getElementById("profile-year-badge").textContent =
      user.school_year || "—";

    document.getElementById("profile-info-name").textContent = user.display_name;
    document.getElementById("profile-info-email").textContent = user.email;
    document.getElementById("profile-info-major").textContent = user.major || "—";
    document.getElementById("profile-info-year").textContent =
      user.school_year || "—";

    document.getElementById(
      "profile-groups-count"
    ).textContent = `${groups.length} group${groups.length === 1 ? "" : "s"}`;

    const groupsListEl = document.getElementById("profile-groups-list");
    groupsListEl.innerHTML = groups.length
      ? groups
          .map(
            (group) => `
        <div class="profile-group-item">
          <div class="info">
            <span class="avatar-circle avatar-small">${escapeHtml(
              group.group_name.charAt(0)
            )}</span>
            <div>
              <h4>${escapeHtml(group.group_name)}</h4>
              <p>${escapeHtml(group.course_code)}</p>
            </div>
          </div>
          <span class="badge ${
            group.creator_user_id === state.user.id ? "badge-purple" : "badge-gray"
          }">${group.creator_user_id === state.user.id ? "Creator" : "Member"}</span>
        </div>
      `
          )
          .join("")
      : `<p class="muted">No groups yet.</p>`;
  } catch (error) {
    showToast(error.message, "error");
  }
}

function setupEditProfile() {
  document.getElementById("open-edit-profile-button").addEventListener("click", () => {
    document.getElementById("edit-profile-name").value = state.user.display_name;
    document.getElementById("edit-profile-major").value = state.user.major || "";
    document.getElementById("edit-profile-year").value = state.user.school_year || "";
    setMessage("edit-profile-message", "");
    document.getElementById("edit-profile-dialog").showModal();
  });

  document
    .getElementById("edit-profile-form")
    .addEventListener("submit", async (event) => {
      event.preventDefault();
      setMessage("edit-profile-message", "");

      const display_name = document.getElementById("edit-profile-name").value.trim();
      const major = document.getElementById("edit-profile-major").value.trim();
      const school_year = document.getElementById("edit-profile-year").value.trim();

      try {
        const updated = await api(`/users/${state.user.id}`, {
          method: "PUT",
          body: JSON.stringify({
            display_name,
            major: major || null,
            school_year: school_year || null,
          }),
        });
        persistUser({ ...state.user, ...updated });
        updateTopbar();
        showToast("Profile updated.");
        document.getElementById("edit-profile-dialog").close();
        loadProfilePage();
      } catch (error) {
        setMessage("edit-profile-message", error.message, "error");
      }
    });

  document.getElementById("logout-button").addEventListener("click", logout);
}

// ----------------------- dialogs (generic close) -----------------------

function setupDialogClosers() {
  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById(button.dataset.closeDialog).close();
    });
  });
}

// ----------------------- boot -----------------------

function init() {
  document.getElementById("login-form").addEventListener("submit", handleLogin);
  document.getElementById("register-form").addEventListener("submit", handleRegister);
  setupAuthSwitcher();
  setupNavigation();
  setupDiscoverGroups();
  setupCreateGroup();
  setupSessionDialog();
  setupDiscussions();
  setupNotifications();
  setupEditProfile();
  setupDialogClosers();

  const persisted = loadPersistedUser();
  if (persisted && persisted.id) {
    state.user = persisted;
    enterApp();
  }
}

document.addEventListener("DOMContentLoaded", init);
