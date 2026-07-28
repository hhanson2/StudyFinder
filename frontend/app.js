const API_BASE_URL = "";

const state = {
    token: sessionStorage.getItem("studyfinder-token"),
    currentUser: null,
    dashboard: null,
    allGroups: [],
    myGroups: [],
    sessions: [],
    selectedGroup: null,
    selectedMembers: [],
    selectedGroupSessions: [],
    selectedPosts: [],
    groupFilter: "all",
    sessionFilter: "upcoming",
    invitations: [], 
};

const viewInformation = {
    dashboard: {
        title: "Dashboard",
        subtitle: "Your study activity at a glance",
    },
    discover: {
        title: "Discover Groups",
        subtitle: "Find a study group for your courses",
    },
    groups: {
        title: "My Groups",
        subtitle: "View and manage your study groups",
    },
    sessions: {
        title: "Sessions",
        subtitle: "Keep track of your study schedule",
    },
    profile: {
        title: "Profile",
        subtitle: "Manage your student information",
    },
};

const authenticationView = document.querySelector("#authentication-view");
const applicationView = document.querySelector("#application-view");
const loginSection = document.querySelector("#login-section");
const registerSection = document.querySelector("#register-section");
const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const toast = document.querySelector("#toast");

let toastTimer;

/* API */

async function apiRequest(path, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });

    if (response.status === 204) {
        return null;
    }

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        if (response.status === 401 && state.token) {
            clearStoredLogin();
            showAuthentication();
        }

        let message = "The request could not be completed.";

        if (typeof data?.detail === "string") {
            message = data.detail;
        } else if (Array.isArray(data?.detail)) {
            message = data.detail
                .map((error) => error.msg)
                .join(" ");
        }

        throw new Error(message);
    }

    return data;
}

/* Authentication */

function saveLogin(response) {
    state.token = response.access_token;
    state.currentUser = response.user;

    sessionStorage.setItem(
        "studyfinder-token",
        state.token,
    );

    sessionStorage.setItem(
        "studyfinderUser",
        JSON.stringify(state.currentUser),
    );
}

function clearStoredLogin() {
    state.token = null;
    state.currentUser = null;
    state.dashboard = null;
    state.allGroups = [];
    state.myGroups = [];
    state.sessions = [];

    sessionStorage.removeItem("studyfinder-token");
    sessionStorage.removeItem("studyfinderUser");
}

function showAuthentication(mode = "login") {
    applicationView.classList.add("hidden");
    authenticationView.classList.remove("hidden");

    const showRegister = mode === "register";

    loginSection.classList.toggle("hidden", showRegister);
    registerSection.classList.toggle("hidden", !showRegister);
}

async function startApplication() {
    authenticationView.classList.add("hidden");
    applicationView.classList.remove("hidden");

    updateUserHeader();
    await showView("dashboard");
}

document
    .querySelector("#show-register-button")
    .addEventListener("click", () => {
        showAuthentication("register");
    });

document
    .querySelector("#show-login-button")
    .addEventListener("click", () => {
        showAuthentication("login");
    });

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.querySelector("#login-message");
    setMessage(message, "Signing in...");

    const loginData = {
        email: document
            .querySelector("#login-email")
            .value
            .trim(),
        password: document
            .querySelector("#login-password")
            .value,
    };

    try {
        const response = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify(loginData),
        });

        saveLogin(response);
        loginForm.reset();
        message.textContent = "";

        await startApplication();
    } catch (error) {
        setMessage(message, error.message, "error");
    }
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.querySelector("#register-message");
    setMessage(message, "Creating your account...");

    const registrationData = {
        display_name: document
            .querySelector("#register-name")
            .value
            .trim(),
        email: document
            .querySelector("#register-email")
            .value
            .trim(),
        password: document
            .querySelector("#register-password")
            .value,
        major: optionalValue("#register-major"),
        school_year: optionalValue("#register-school-year"),
    };

    try {
        const response = await apiRequest("/auth/register", {
            method: "POST",
            body: JSON.stringify(registrationData),
        });

        saveLogin(response);
        registerForm.reset();
        message.textContent = "";

        await startApplication();
        showToast("Account created successfully.");
    } catch (error) {
        setMessage(message, error.message, "error");
    }
});

document
    .querySelector("#logout-button")
    .addEventListener("click", () => {
        clearStoredLogin();
        showAuthentication("login");
    });

/* Navigation */

document.addEventListener("click", async (event) => {
    const viewButton = event.target.closest("[data-view]");

    if (viewButton) {
        await showView(viewButton.dataset.view);
    }
});

async function showView(viewName) {
    if (!viewInformation[viewName]) {
        return;
    }

    document
        .querySelectorAll(".view-section")
        .forEach((section) => {
            section.classList.add("hidden");
        });

    document
        .querySelector(`#${viewName}-view`)
        .classList.remove("hidden");

    document
        .querySelectorAll(".navigation-link")
        .forEach((button) => {
            button.classList.toggle(
                "active",
                button.dataset.view === viewName,
            );
        });

    document.querySelector("#page-title").textContent =
        viewInformation[viewName].title;

    document.querySelector("#page-subtitle").textContent =
        viewInformation[viewName].subtitle;

    if (viewName === "dashboard") {
        await loadDashboard();
    } else if (viewName === "discover") {
        await loadDiscoverGroups();
    } else if (viewName === "groups") {
        await loadMyGroups();
    } else if (viewName === "sessions") {
        await loadSessions();
    } else if (viewName === "profile") {
        await loadProfile();
    }
}

function updateUserHeader() {
    if (!state.currentUser) {
        return;
    }

    document.querySelector("#header-user-name").textContent =
        state.currentUser.display_name;

    document.querySelector("#header-user-initials").textContent =
        getInitials(state.currentUser.display_name);

    document.querySelector("#header-user-role").textContent =
        state.currentUser.major ||
        state.currentUser.school_year ||
        "Student";
}

/* Dashboard */

async function loadDashboard() {
    try {
        const [dashboard, invitations] = await Promise.all([
            apiRequest("/dashboard/"),
            apiRequest("/invitations/mine"),
        ]);

        state.dashboard = dashboard;
        state.invitations = invitations;
        state.currentUser = dashboard.user;

        sessionStorage.setItem(
            "studyfinderUser",
            JSON.stringify(state.currentUser),
        );

        updateUserHeader();
        renderDashboard();
        renderInvitations();
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderDashboard() {
    const dashboard = state.dashboard;
    const summary = dashboard.summary;

    document.querySelector("#day-period").textContent =
        getDayPeriod();

    document.querySelector("#greeting-name").textContent =
        getFirstName(state.currentUser.display_name);

    document.querySelector("#dashboard-joined-count").textContent =
        summary.joined_groups;

    document.querySelector("#dashboard-created-count").textContent =
        summary.created_groups;

    document.querySelector("#dashboard-session-count").textContent =
        summary.upcoming_sessions;

    document.querySelector("#dashboard-post-count").textContent =
        summary.discussion_posts;

    const sessionWord =
        summary.upcoming_sessions === 1
            ? "session"
            : "sessions";

    document.querySelector(
        "#dashboard-session-message",
    ).textContent =
        summary.upcoming_sessions === 0
            ? "You have no upcoming study sessions."
            : `You have ${summary.upcoming_sessions} upcoming ${sessionWord}.`;

    renderDashboardSessions(dashboard.upcoming_sessions);
    renderDashboardGroups(dashboard.my_groups);
}




function renderInvitations() {
    const container = document.querySelector("#invitations-list");
    const count = document.querySelector(
        "#pending-invitation-count",
    );

    const pendingInvitations = state.invitations.filter(
        (invitation) => invitation.status === "pending",
    );

    count.textContent =
        `${pendingInvitations.length} pending`;

    if (!pendingInvitations.length) {
        container.innerHTML = `
            <div class="empty-state">
                <p>You have no pending invitations.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = pendingInvitations
        .map((invitation) => {
            const invitationName =
                invitation.invitation_type === "group"
                    ? invitation.group_name
                    : invitation.session_title;

            return `
                <article class="invitation-item">
                    <div>
                        <strong>
                            ${escapeHTML(
                                invitationName || "Invitation",
                            )}
                        </strong>

                        <p>
                            Invited by
                            ${escapeHTML(
                                invitation.inviter_name || "a user",
                            )}
                        </p>
                    </div>

                    <div class="invitation-actions">
                        <button
                            class="primary-button"
                            data-accept-invitation="${invitation.id}"
                            type="button"
                        >
                            Accept
                        </button>

                        <button
                            class="secondary-button"
                            data-decline-invitation="${invitation.id}"
                            type="button"
                        >
                            Decline
                        </button>
                    </div>
                </article>
            `;
        })
        .join("");
}








    document.addEventListener("click", async (event) => {
    const acceptButton = event.target.closest(
        "[data-accept-invitation]",
    );

    const declineButton = event.target.closest(
        "[data-decline-invitation]",
    );

    if (acceptButton) {
        const invitationId = Number(
            acceptButton.dataset.acceptInvitation,
        );

        await respondToInvitation(
            invitationId,
            "accept",
        );
    }

    if (declineButton) {
        const invitationId = Number(
            declineButton.dataset.declineInvitation,
        );

        await respondToInvitation(
            invitationId,
            "decline",
        );
    }
});

async function respondToInvitation(
    invitationId,
    response,
) {
    try {
        await apiRequest(
            `/invitations/${invitationId}/${response}`,
            {
                method: "PUT",
            },
        );

        showToast(
            response === "accept"
                ? "Invitation accepted."
                : "Invitation declined.",
        );

        await Promise.all([
            loadDashboard(),
            loadMyGroups(),
            loadSessions(),
        ]);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderDashboardSessions(sessions) {
    const container = document.querySelector(
        "#dashboard-sessions-list",
    );

    if (!sessions.length) {
        container.innerHTML = emptyState(
            "You have no upcoming study sessions.",
        );
        return;
    }

    container.innerHTML = sessions
        .map((session) => sessionListItem(session, false))
        .join("");
}

function renderDashboardGroups(groups) {
    const container = document.querySelector(
        "#dashboard-groups-list",
    );

    if (!groups.length) {
        container.innerHTML = emptyState(
            "You have not joined any study groups.",
        );
        return;
    }

    container.innerHTML = groups
        .slice(0, 3)
        .map((group) => {
            const role =
                group.creator_user_id === state.currentUser.id
                    ? "Creator"
                    : "Member";

            return `
                <button
                    class="quick-group"
                    data-open-group="${group.id}"
                    type="button"
                >
                    <span class="item-icon">
                        ${escapeHTML(group.course_code.charAt(0))}
                    </span>

                    <span class="item-information">
                        <strong>${escapeHTML(group.group_name)}</strong>
                        <small>${escapeHTML(group.course_code)}</small>
                    </span>

                    <span class="badge">${role}</span>
                </button>
            `;
        })
        .join("");
}

/* Discover groups */

document
    .querySelector("#group-search-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();
        await loadDiscoverGroups();
    });

async function loadDiscoverGroups() {
    const searchValue = document
        .querySelector("#group-search-input")
        .value
        .trim();

    const query = searchValue
        ? `?course_code=${encodeURIComponent(searchValue)}`
        : "";

    const message = document.querySelector(
        "#group-search-message",
    );

    setMessage(message, "Loading study groups...");

    try {
        const [groups, invitations] = await Promise.all([
    apiRequest(`/study-groups/${query}`),
    apiRequest("/invitations/mine"),
]);

state.invitations = invitations;

        await Promise.all(
            groups.map(async (group) => {
                const members = await apiRequest(
                    `/study-groups/${group.id}/members`,
                );

                group.members = members;
                group.member_count = members.length;
                group.is_member = members.some(
                    (member) =>
                        member.user_id === state.currentUser.id,
                );
            }),
        );

        state.allGroups = groups;
        message.textContent = "";
        renderDiscoverGroups();
    } catch (error) {
        setMessage(message, error.message, "error");
    }
}

function renderDiscoverGroups() {
    const container = document.querySelector(
        "#discover-groups-list",
    );

    if (!state.allGroups.length) {
        container.innerHTML = emptyState(
            "No matching study groups were found.",
        );
        return;
    }

    container.innerHTML = state.allGroups
        .map((group) => groupCard(group, "discover"))
        .join("");
}














/* My groups */

async function loadMyGroups() {
    try {
        state.myGroups = await apiRequest(
            "/users/me/study-groups",
        );

        renderMyGroups();
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderMyGroups() {
    const container = document.querySelector("#my-groups-list");

    const filteredGroups = state.myGroups.filter((group) => {
        if (state.groupFilter === "created") {
            return group.is_creator;
        }

        if (state.groupFilter === "joined") {
            return !group.is_creator;
        }

        return true;
    });

    if (!filteredGroups.length) {
        container.innerHTML = emptyState(
            "No study groups match this filter.",
        );
        return;
    }

    container.innerHTML = filteredGroups
        .map((group) => groupCard(group, "mine"))
        .join("");
}

document
    .querySelectorAll("[data-group-filter]")
    .forEach((button) => {
        button.addEventListener("click", () => {
            state.groupFilter = button.dataset.groupFilter;

            document
                .querySelectorAll("[data-group-filter]")
                .forEach((item) => {
                    item.classList.toggle(
                        "active",
                        item === button,
                    );
                });

            renderMyGroups();
        });
    });

/* Group cards and membership */

function groupCard(group, source) {
    const isCreator =
        group.creator_user_id === state.currentUser.id ||
        group.is_creator;

    const isMember =
        isCreator ||
        group.is_member ||
        source === "mine";

    const memberCount =
        group.member_count ?? group.members?.length ?? 0;


    const hasPendingInvitation = state.invitations.some(
    (invitation) =>
        invitation.invitation_type === "group" &&
        Number(invitation.group_id) === Number(group.id) &&
        invitation.status === "pending",
);


    let membershipAction = "";

if (source === "discover" && !isCreator) {
    if (isMember) {
        membershipAction = `
            <button
                class="danger-button"
                data-leave-group="${group.id}"
                type="button"
            >
                Leave
            </button>
        `;
    } else if (hasPendingInvitation) {
        membershipAction = `
            <button
                class="primary-button"
                data-join-group="${group.id}"
                type="button"
            >
                Join
            </button>
        `;
    } else {
        membershipAction = `
            <button
                class="secondary-button"
                type="button"
                disabled
            >
                Invitation required
            </button>
        `;
    }
}

    const creatorAction = isCreator
        ? `
            <button
                class="secondary-button"
                data-edit-group="${group.id}"
                type="button"
            >
                Edit
            </button>
        `
        : "";

    return `
        <article class="group-card">
            <div class="group-card-header">
                <span class="course-code">
                    ${escapeHTML(group.course_code)}
                </span>

                <span class="badge ${
                    group.status === "open" ? "success" : "warning"
                }">
                    ${escapeHTML(group.status)}
                </span>
            </div>

            <h2>${escapeHTML(group.group_name)}</h2>

            <p>
                ${escapeHTML(
                    group.description || "No description provided.",
                )}
            </p>

            <div class="group-card-meta">
                <span>
                    ${memberCount} of ${group.max_members} members
                </span>

                ${isCreator ? "<span>Created by you</span>" : ""}
            </div>

            <div class="group-card-actions">
                <button
                    class="secondary-button"
                    data-open-group="${group.id}"
                    type="button"
                >
                    Details
                </button>

                ${creatorAction}
                ${membershipAction}
            </div>
        </article>
    `;
}

document.addEventListener("click", async (event) => {
    const openButton = event.target.closest("[data-open-group]");
    const joinButton = event.target.closest("[data-join-group]");
    const leaveButton = event.target.closest("[data-leave-group]");
    const editButton = event.target.closest("[data-edit-group]");

    if (openButton) {
        await openGroupDetails(Number(openButton.dataset.openGroup));
    } else if (joinButton) {
        await joinGroup(Number(joinButton.dataset.joinGroup));
    } else if (leaveButton) {
        await leaveGroup(Number(leaveButton.dataset.leaveGroup));
    } else if (editButton) {
        await openEditGroupForm(Number(editButton.dataset.editGroup));
    }
});

async function joinGroup(groupId) {
    try {
        await apiRequest(
            `/study-groups/${groupId}/members/me`,
            { method: "POST" },
        );

        showToast("You joined the study group.");
        await refreshGroupData();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function leaveGroup(groupId) {
    if (!window.confirm("Leave this study group?")) {
        return;
    }

    try {
        await apiRequest(
            `/study-groups/${groupId}/members/me`,
            { method: "DELETE" },
        );

        document.querySelector("#group-details-dialog").close();
        showToast("You left the study group.");
        await refreshGroupData();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function refreshGroupData() {
    await Promise.all([
        loadDashboard(),
        loadMyGroups(),
        loadDiscoverGroups(),
    ]);
}

/* Create and edit groups */

document
    .querySelectorAll(".open-group-form")
    .forEach((button) => {
        button.addEventListener("click", openCreateGroupForm);
    });

document
    .querySelector("#quick-create-group")
    .addEventListener("click", openCreateGroupForm);

function openCreateGroupForm() {
    const form = document.querySelector("#group-form");
    form.reset();

    document.querySelector("#editing-group-id").value = "";
    document.querySelector("#group-capacity-input").value = "10";
    document.querySelector("#group-status-input").value = "open";
    document.querySelector("#group-form-title").textContent =
        "Create a study group";
    document.querySelector("#group-form-message").textContent = "";

    document.querySelector("#group-form-dialog").showModal();
}

async function openEditGroupForm(groupId) {
    try {
        const group = await apiRequest(`/study-groups/${groupId}`);

        document.querySelector("#editing-group-id").value =
            group.id;
        document.querySelector("#group-name-input").value =
            group.group_name;
        document.querySelector("#course-code-input").value =
            group.course_code;
        document.querySelector("#group-description-input").value =
            group.description || "";
        document.querySelector("#group-capacity-input").value =
            group.max_members;
        document.querySelector("#group-status-input").value =
            group.status;
        document.querySelector("#group-form-title").textContent =
            "Edit study group";
        document.querySelector("#group-form-message").textContent = "";

        document.querySelector("#group-form-dialog").showModal();
    } catch (error) {
        showToast(error.message, "error");
    }
}

document
    .querySelector("#group-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const groupId = document
            .querySelector("#editing-group-id")
            .value;

        const groupData = {
            group_name: document
                .querySelector("#group-name-input")
                .value
                .trim(),
            course_code: document
                .querySelector("#course-code-input")
                .value
                .trim(),
            description:
                optionalValue("#group-description-input"),
            status: document.querySelector("#group-status-input").value,
            max_members: Number(
                document.querySelector("#group-capacity-input").value,
            ),
        };

        const message = document.querySelector(
            "#group-form-message",
        );

        try {
            await apiRequest(
                groupId
                    ? `/study-groups/${groupId}`
                    : "/study-groups/",
                {
                    method: groupId ? "PUT" : "POST",
                    body: JSON.stringify(groupData),
                },
            );

            document.querySelector("#group-form-dialog").close();
            showToast(
                groupId
                    ? "Study group updated."
                    : "Study group created.",
            );

            await refreshGroupData();
        } catch (error) {
            setMessage(message, error.message, "error");
        }
    });

/* Group details */

async function openGroupDetails(groupId) {
    try {
        const [group, members] = await Promise.all([
            apiRequest(`/study-groups/${groupId}`),
            apiRequest(`/study-groups/${groupId}/members`),
        ]);

        state.selectedGroup = group;
        state.selectedMembers = members;

        document.querySelector("#detail-course-code").textContent =
            group.course_code;

        document.querySelector("#detail-group-name").textContent =
            group.group_name;

        renderGroupDetailActions();
        renderGroupOverview();
        renderGroupMembers();
        selectDetailTab("overview");

        document.querySelector("#group-details-dialog").showModal();
    } catch (error) {
        showToast(error.message, "error");
    }
}

function selectedGroupIsCreator() {
    return (
        state.selectedGroup?.creator_user_id ===
        state.currentUser.id
    );
}

function selectedGroupIsMember() {
    return state.selectedMembers.some(
        (member) => member.user_id === state.currentUser.id,
    );
}

function renderGroupDetailActions() {
    const container = document.querySelector(
        "#group-detail-actions",
    );

    const group = state.selectedGroup;
    const isCreator = selectedGroupIsCreator();
    const isMember = selectedGroupIsMember();

    if (isCreator) {
        container.innerHTML = `
            <button
                class="secondary-button"
                data-edit-selected-group
                type="button"
            >
                Edit group
            </button>

            <button
                class="secondary-button"
                data-invite-group="${group.id}"
                type="button"
            >
                Invite user
            </button>

            <button
                class="primary-button"
                data-create-session="${group.id}"
                type="button"
            >
                Schedule session
            </button>

            <button
                class="danger-button"
                data-delete-group="${group.id}"
                type="button"
            >
                Delete group
            </button>
        `;
    } else if (isMember) {
        container.innerHTML = `
            <button
                class="danger-button"
                data-leave-group="${group.id}"
                type="button"
            >
                Leave group
            </button>
        `;
    } else {
        container.innerHTML = `
            <button
                class="primary-button"
                data-join-group="${group.id}"
                type="button"
                ${group.status !== "open" ? "disabled" : ""}
            >
                ${
                    group.status === "open"
                        ? "Join group"
                        : "Group closed"
                }
            </button>
        `;
    }
}

function renderGroupOverview() {
    const group = state.selectedGroup;

    document.querySelector("#detail-overview-panel").innerHTML = `
        <div class="detail-section">
            <h3>About this group</h3>

            <p>
                ${escapeHTML(
                    group.description || "No description provided.",
                )}
            </p>
        </div>

        <div class="detail-stat-grid">
            <div>
                <strong>${escapeHTML(group.status)}</strong>
                <span>Status</span>
            </div>

            <div>
                <strong>
                    ${state.selectedMembers.length}
                    / ${group.max_members}
                </strong>
                <span>Members</span>
            </div>

            <div>
                <strong>${escapeHTML(group.course_code)}</strong>
                <span>Course</span>
            </div>
        </div>
    `;
}

function renderGroupMembers() {
    const container = document.querySelector(
        "#detail-members-panel",
    );

    if (!state.selectedMembers.length) {
        container.innerHTML = emptyState(
            "This group does not have any members.",
        );
        return;
    }

    container.innerHTML = `
        <div class="item-list">
            ${state.selectedMembers
                .map(
                    (member) => `
                        <article class="list-item">
                            <div class="item-main">
                                <span class="item-icon">
                                    ${escapeHTML(
                                        member.display_name.charAt(0),
                                    )}
                                </span>

                                <div class="item-information">
                                    <h3>
                                        ${escapeHTML(member.display_name)}
                                    </h3>

                                    <p>${escapeHTML(member.email)}</p>
                                </div>
                            </div>
                        </article>
                    `,
                )
                .join("")}
        </div>
    `;
}

document.addEventListener("click", async (event) => {
    if (event.target.closest("[data-edit-selected-group]")) {
        document.querySelector("#group-details-dialog").close();
        await openEditGroupForm(state.selectedGroup.id);
    }

    const deleteButton = event.target.closest("[data-delete-group]");

    if (deleteButton) {
        await deleteGroup(Number(deleteButton.dataset.deleteGroup));
    }
});

async function deleteGroup(groupId) {
    if (
        !window.confirm(
            "Delete this study group and all of its sessions and discussions?",
        )
    ) {
        return;
    }

    try {
        await apiRequest(`/study-groups/${groupId}`, {
            method: "DELETE",
        });

        document.querySelector("#group-details-dialog").close();
        showToast("Study group deleted.");
        await refreshGroupData();
    } catch (error) {
        showToast(error.message, "error");
    }
}

document
    .querySelectorAll("[data-detail-tab]")
    .forEach((button) => {
        button.addEventListener("click", async () => {
            await selectDetailTab(button.dataset.detailTab);
        });
    });

async function selectDetailTab(tabName) {
    document
        .querySelectorAll("[data-detail-tab]")
        .forEach((button) => {
            button.classList.toggle(
                "active",
                button.dataset.detailTab === tabName,
            );
        });

    document
        .querySelectorAll(".detail-panel")
        .forEach((panel) => panel.classList.add("hidden"));

    document
        .querySelector(`#detail-${tabName}-panel`)
        .classList.remove("hidden");

    if (tabName === "sessions") {
        await loadSelectedGroupSessions();
    } else if (tabName === "discussion") {
        await loadSelectedGroupPosts();
    }
}


document.addEventListener("click", async (event) => {
    const inviteButton = event.target.closest(
        "[data-invite-group]",
    );

    if (!inviteButton) {
        return;
    }

    const groupId = Number(
        inviteButton.dataset.inviteGroup,
    );

    const email = window.prompt(
        "Enter the registered user's email:",
    );

    if (!email || !email.trim()) {
        return;
    }

    try {
        await apiRequest(
            `/invitations/groups/${groupId}`,
            {
                method: "POST",
                body: JSON.stringify({
                    invitee_email: email.trim(),
                }),
            },
        );

        showToast(
    `Invitation successfully sent to ${email.trim()}.`,
);

        showToast("Group invitation sent.");
    } catch (error) {
        showToast(error.message, "error");
    }
});















/* Sessions */

async function loadSessions() {
    try {
        state.sessions = await apiRequest("/users/me/sessions");

        if (!state.myGroups.length) {
            state.myGroups = await apiRequest(
                "/users/me/study-groups",
            );
        }

        renderSessions();
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderSessions() {
    const now = new Date();

    const filtered = state.sessions.filter((session) => {
        const sessionDate = new Date(session.scheduled_at);

        return state.sessionFilter === "upcoming"
            ? sessionDate >= now
            : sessionDate < now;
    });

    const container = document.querySelector("#sessions-list");

    if (!filtered.length) {
        container.innerHTML = emptyState(
            `You have no ${state.sessionFilter} sessions.`,
        );
        return;
    }

    container.innerHTML = filtered
        .map((session) => sessionListItem(session, true))
        .join("");
}

function sessionListItem(session, includeActions) {
    const location =
        session.location ||
        (session.meeting_link ? "Online meeting" : "Location not set");

    const actions =
        includeActions && session.can_manage
            ? `
                <div class="item-actions">



                <button
    class="secondary-button"
    data-invite-session="${session.id}"
    type="button"
>
    Invite member
</button>

                    <button
                        class="secondary-button"
                        data-edit-session="${session.id}"
                        type="button"
                    >
                        Edit
                    </button>

                    <button
                        class="danger-button"
                        data-delete-session="${session.id}"
                        type="button"
                    >
                        Delete
                    </button>
                </div>
            `
            : "";

    return `
        <article class="list-item">
            <div class="item-main">
                <span class="item-icon">□</span>

                <div class="item-information">
                    <h3>${escapeHTML(session.title)}</h3>

                    <p>
                        ${escapeHTML(session.course_code)}
                        •
                        ${escapeHTML(session.group_name)}
                    </p>

                    <div class="item-meta">
                        <span>${formatDateTime(session.scheduled_at)}</span>
                        <span>${escapeHTML(location)}</span>
                        <span>${session.duration_minutes} minutes</span>
                    </div>
                </div>
            </div>

            ${actions}
        </article>
    `;
}

document
    .querySelectorAll("[data-session-filter]")
    .forEach((button) => {
        button.addEventListener("click", () => {
            state.sessionFilter = button.dataset.sessionFilter;

            document
                .querySelectorAll("[data-session-filter]")
                .forEach((item) => {
                    item.classList.toggle(
                        "active",
                        item === button,
                    );
                });

            renderSessions();
        });
    });

document
    .querySelector("#open-session-form")
    .addEventListener("click", () => {
        openCreateSessionForm();
    });

document.addEventListener("click", async (event) => {
    const createButton = event.target.closest("[data-create-session]");
    const editButton = event.target.closest("[data-edit-session]");
    const deleteButton = event.target.closest("[data-delete-session]");

    if (createButton) {
        openCreateSessionForm(
            Number(createButton.dataset.createSession),
        );
    } else if (editButton) {
        await openEditSessionForm(
            Number(editButton.dataset.editSession),
        );
    } else if (deleteButton) {
        await deleteSession(
            Number(deleteButton.dataset.deleteSession),
        );
    }
});




document.addEventListener("click", async (event) => {
    const inviteButton = event.target.closest(
        "[data-invite-session]",
    );

    if (!inviteButton) {
        return;
    }

    const sessionId = Number(
        inviteButton.dataset.inviteSession,
    );

    const email = window.prompt(
        "Enter the group member's email:",
    );

    if (!email || !email.trim()) {
        return;
    }

    try {
        await apiRequest(
            `/invitations/sessions/${sessionId}`,
            {
                method: "POST",
                body: JSON.stringify({
                    invitee_email: email.trim(),
                }),
            },
        );

        showToast(
            `Session invitation successfully sent to ${email.trim()}.`,
        );
    } catch (error) {
        showToast(error.message, "error");
    }
});






async function ensureMyGroupsLoaded() {
    if (!state.myGroups.length) {
        state.myGroups = await apiRequest(
            "/users/me/study-groups",
        );
    }
}

async function openCreateSessionForm(selectedGroupId = null) {
    try {
        await ensureMyGroupsLoaded();

        const createdGroups = state.myGroups.filter(
            (group) => group.is_creator,
        );

        if (!createdGroups.length) {
            showToast(
                "Create a study group before scheduling a session.",
                "error",
            );
            return;
        }

        const form = document.querySelector("#session-form");
        form.reset();

        document.querySelector("#editing-session-id").value = "";
        document.querySelector("#session-form-title").textContent =
            "Schedule a study session";
        document.querySelector("#session-duration-input").value = "60";
        document.querySelector("#session-group-input").disabled = false;
        document.querySelector("#session-form-message").textContent = "";

        populateSessionGroupOptions(
            createdGroups,
            selectedGroupId,
        );

        document.querySelector("#session-form-dialog").showModal();
    } catch (error) {
        showToast(error.message, "error");
    }
}

function populateSessionGroupOptions(groups, selectedGroupId = null) {
    const select = document.querySelector("#session-group-input");

    select.innerHTML = groups
        .map(
            (group) => `
                <option
                    value="${group.id}"
                    ${
                        group.id === selectedGroupId
                            ? "selected"
                            : ""
                    }
                >
                    ${escapeHTML(group.course_code)}
                    — ${escapeHTML(group.group_name)}
                </option>
            `,
        )
        .join("");
}

async function openEditSessionForm(sessionId) {
    try {
        const session = await apiRequest(`/sessions/${sessionId}`);

        await ensureMyGroupsLoaded();

        const group = state.myGroups.find(
            (item) => item.id === session.group_id,
        );

        if (!group?.is_creator) {
            showToast(
                "Only the group creator can edit this session.",
                "error",
            );
            return;
        }

        populateSessionGroupOptions([group], group.id);

        document.querySelector("#editing-session-id").value =
            session.id;
        document.querySelector("#session-group-input").disabled = true;
        document.querySelector("#session-title-input").value =
            session.title;
        document.querySelector("#session-date-input").value =
            toDateTimeLocal(session.scheduled_at);
        document.querySelector("#session-duration-input").value =
            session.duration_minutes;
        document.querySelector("#session-location-input").value =
            session.location || "";
        document.querySelector("#session-link-input").value =
            session.meeting_link || "";
        document.querySelector("#session-form-title").textContent =
            "Edit study session";
        document.querySelector("#session-form-message").textContent = "";

        document.querySelector("#session-form-dialog").showModal();
    } catch (error) {
        showToast(error.message, "error");
    }
}

document
    .querySelector("#session-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const sessionId = document
            .querySelector("#editing-session-id")
            .value;

        const groupId = Number(
            document.querySelector("#session-group-input").value,
        );

        const sessionData = {
            title: document
                .querySelector("#session-title-input")
                .value
                .trim(),
            scheduled_at: document.querySelector(
                "#session-date-input",
            ).value,
            duration_minutes: Number(
                document.querySelector(
                    "#session-duration-input",
                ).value,
            ),
            location: optionalValue("#session-location-input"),
            meeting_link: optionalValue("#session-link-input"),
        };

        const message = document.querySelector(
            "#session-form-message",
        );

        try {
            await apiRequest(
                sessionId
                    ? `/sessions/${sessionId}`
                    : `/study-groups/${groupId}/sessions`,
                {
                    method: sessionId ? "PUT" : "POST",
                    body: JSON.stringify(sessionData),
                },
            );

            document.querySelector("#session-form-dialog").close();
            showToast(
                sessionId
                    ? "Study session updated."
                    : "Study session scheduled.",
            );

            await Promise.all([loadSessions(), loadDashboard()]);

            if (
                state.selectedGroup &&
                state.selectedGroup.id === groupId
            ) {
                await loadSelectedGroupSessions();
            }
        } catch (error) {
            setMessage(message, error.message, "error");
        }
    });

async function deleteSession(sessionId) {
    if (!window.confirm("Delete this study session?")) {
        return;
    }

    try {
        await apiRequest(`/sessions/${sessionId}`, {
            method: "DELETE",
        });

        showToast("Study session deleted.");
        await Promise.all([loadSessions(), loadDashboard()]);

        if (state.selectedGroup) {
            await loadSelectedGroupSessions();
        }
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function loadSelectedGroupSessions() {
    const container = document.querySelector(
        "#detail-sessions-panel",
    );

    if (!selectedGroupIsMember()) {
        container.innerHTML = emptyState(
            "Join this group to view its sessions.",
        );
        return;
    }

    try {
        state.selectedGroupSessions = await apiRequest(
            `/study-groups/${state.selectedGroup.id}/sessions`,
        );

        if (!state.selectedGroupSessions.length) {
            container.innerHTML = emptyState(
                "No study sessions have been scheduled.",
            );
            return;
        }

        container.innerHTML = `
            <div class="item-list">
                ${state.selectedGroupSessions
                    .map((session) => {
                        const expanded = {
                            ...session,
                            group_name: state.selectedGroup.group_name,
                            course_code: state.selectedGroup.course_code,
                            can_manage: selectedGroupIsCreator(),
                        };

                        return sessionListItem(expanded, true);
                    })
                    .join("")}
            </div>
        `;
    } catch (error) {
        container.innerHTML = emptyState(error.message);
    }
}














/* Discussions */

async function loadSelectedGroupPosts() {
    const container = document.querySelector(
        "#detail-discussion-panel",
    );

    if (!selectedGroupIsMember()) {
        container.innerHTML = emptyState(
            "Join this group to access its discussion.",
        );
        return;
    }

    try {
        state.selectedPosts = await apiRequest(
            `/study-groups/${state.selectedGroup.id}/posts`,
        );

        renderSelectedGroupPosts();
    } catch (error) {
        container.innerHTML = emptyState(error.message);
    }
}

function renderSelectedGroupPosts() {
    const container = document.querySelector(
        "#detail-discussion-panel",
    );

    const createButton = `
        <div class="discussion-toolbar">
            <button
                class="primary-button"
                data-create-post="${state.selectedGroup.id}"
                type="button"
            >
                Create post
            </button>
        </div>
    `;

    if (!state.selectedPosts.length) {
        container.innerHTML =
            createButton +
            emptyState("No discussion posts have been created.");
        return;
    }

    container.innerHTML =
        createButton +
        `
            <div class="discussion-list">
                ${state.selectedPosts
                    .map((post) => postCard(post))
                    .join("")}
            </div>
        `;
}

function postCard(post) {
    const isAuthor = post.user_id === state.currentUser.id;

    return `
        <article class="discussion-post">
            <header>
                <div>
                    <h3>${escapeHTML(post.title)}</h3>

                    <p>
                        ${escapeHTML(post.display_name)}
                        • ${formatDateTime(post.created_at)}
                    </p>
                </div>

                ${
                    isAuthor
                        ? `
                            <div class="item-actions">
                                <button
                                    class="text-button"
                                    data-edit-post="${post.id}"
                                    type="button"
                                >
                                    Edit
                                </button>

                                <button
                                    class="text-button danger-text"
                                    data-delete-post="${post.id}"
                                    type="button"
                                >
                                    Delete
                                </button>
                            </div>
                        `
                        : ""
                }
            </header>

            <p>${escapeHTML(post.content)}</p>

            <button
                class="text-button"
                data-toggle-replies="${post.id}"
                type="button"
            >
                View replies
            </button>

            <div
                id="replies-${post.id}"
                class="reply-section hidden"
            ></div>
        </article>
    `;
}

document.addEventListener("click", async (event) => {
    const createButton = event.target.closest("[data-create-post]");
    const editButton = event.target.closest("[data-edit-post]");
    const deleteButton = event.target.closest("[data-delete-post]");
    const repliesButton = event.target.closest("[data-toggle-replies]");

    if (createButton) {
        openCreatePostForm(Number(createButton.dataset.createPost));
    } else if (editButton) {
        openEditPostForm(Number(editButton.dataset.editPost));
    } else if (deleteButton) {
        await deletePost(Number(deleteButton.dataset.deletePost));
    } else if (repliesButton) {
        await toggleReplies(Number(repliesButton.dataset.toggleReplies));
    }
});

function openCreatePostForm(groupId) {
    document.querySelector("#post-form").reset();
    document.querySelector("#post-group-id").value = groupId;
    document.querySelector("#editing-post-id").value = "";
    document.querySelector("#post-form-title").textContent =
        "Create a discussion post";
    document.querySelector("#post-form-message").textContent = "";
    document.querySelector("#post-form-dialog").showModal();
}

function openEditPostForm(postId) {
    const post = state.selectedPosts.find(
        (item) => item.id === postId,
    );

    if (!post) {
        return;
    }

    document.querySelector("#post-group-id").value = post.group_id;
    document.querySelector("#editing-post-id").value = post.id;
    document.querySelector("#post-title-input").value = post.title;
    document.querySelector("#post-content-input").value = post.content;
    document.querySelector("#post-form-title").textContent =
        "Edit discussion post";
    document.querySelector("#post-form-message").textContent = "";
    document.querySelector("#post-form-dialog").showModal();
}

document
    .querySelector("#post-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const postId = document
            .querySelector("#editing-post-id")
            .value;

        const groupId = Number(
            document.querySelector("#post-group-id").value,
        );

        const postData = {
            title: document
                .querySelector("#post-title-input")
                .value
                .trim(),
            content: document
                .querySelector("#post-content-input")
                .value
                .trim(),
        };

        const message = document.querySelector("#post-form-message");

        try {
            await apiRequest(
                postId
                    ? `/posts/${postId}`
                    : `/study-groups/${groupId}/posts`,
                {
                    method: postId ? "PUT" : "POST",
                    body: JSON.stringify(postData),
                },
            );

            document.querySelector("#post-form-dialog").close();
            showToast(postId ? "Post updated." : "Post created.");

            await Promise.all([
                loadSelectedGroupPosts(),
                loadDashboard(),
            ]);
        } catch (error) {
            setMessage(message, error.message, "error");
        }
    });

async function deletePost(postId) {
    if (!window.confirm("Delete this discussion post?")) {
        return;
    }

    try {
        await apiRequest(`/posts/${postId}`, {
            method: "DELETE",
        });

        showToast("Post deleted.");

        await Promise.all([
            loadSelectedGroupPosts(),
            loadDashboard(),
        ]);
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function toggleReplies(postId) {
    const container = document.querySelector(`#replies-${postId}`);

    if (!container.classList.contains("hidden")) {
        container.classList.add("hidden");
        return;
    }

    container.classList.remove("hidden");
    container.innerHTML = "<p>Loading replies...</p>";

    try {
        const replies = await apiRequest(
            `/posts/${postId}/replies`,
        );

        renderReplies(postId, replies);
    } catch (error) {
        container.innerHTML = emptyState(error.message);
    }
}

function renderReplies(postId, replies) {
    const container = document.querySelector(`#replies-${postId}`);

    container.innerHTML = `
        <div class="reply-list">
            ${
                replies.length
                    ? replies.map((reply) => replyCard(reply)).join("")
                    : '<p class="muted-text">No replies yet.</p>'
            }
        </div>

        <form
            class="reply-form"
            data-reply-form="${postId}"
        >
            <input
                name="content"
                type="text"
                placeholder="Write a reply"
                required
            >

            <button
                class="primary-button"
                type="submit"
            >
                Reply
            </button>
        </form>
    `;
}

function replyCard(reply) {
    const isAuthor = reply.user_id === state.currentUser.id;

    return `
        <article class="reply-item">
            <div>
                <strong>${escapeHTML(reply.display_name)}</strong>
                <span>${formatDateTime(reply.created_at)}</span>
                <p>${escapeHTML(reply.content)}</p>
            </div>

            ${
                isAuthor
                    ? `
                        <div class="item-actions">
                            <button
                                class="text-button"
                                data-edit-reply="${reply.id}"
                                data-reply-content="${escapeAttribute(
                                    reply.content,
                                )}"
                                type="button"
                            >
                                Edit
                            </button>

                            <button
                                class="text-button danger-text"
                                data-delete-reply="${reply.id}"
                                type="button"
                            >
                                Delete
                            </button>
                        </div>
                    `
                    : ""
            }
        </article>
    `;
}

document.addEventListener("submit", async (event) => {
    const replyForm = event.target.closest("[data-reply-form]");

    if (!replyForm) {
        return;
    }

    event.preventDefault();

    const postId = Number(replyForm.dataset.replyForm);
    const content = replyForm.elements.content.value.trim();

    try {
        await apiRequest(`/posts/${postId}/replies`, {
            method: "POST",
            body: JSON.stringify({ content }),
        });

        const replies = await apiRequest(
            `/posts/${postId}/replies`,
        );

        renderReplies(postId, replies);
    } catch (error) {
        showToast(error.message, "error");
    }
});

document.addEventListener("click", async (event) => {
    const editButton = event.target.closest("[data-edit-reply]");
    const deleteButton = event.target.closest("[data-delete-reply]");

    if (editButton) {
        const replyId = Number(editButton.dataset.editReply);
        const existingContent = editButton.dataset.replyContent;

        const content = window.prompt(
            "Edit your reply:",
            existingContent,
        );

        if (content === null || !content.trim()) {
            return;
        }

        try {
            await apiRequest(`/replies/${replyId}`, {
                method: "PUT",
                body: JSON.stringify({ content: content.trim() }),
            });

            await loadSelectedGroupPosts();
            showToast("Reply updated.");
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    if (deleteButton) {
        const replyId = Number(deleteButton.dataset.deleteReply);

        if (!window.confirm("Delete this reply?")) {
            return;
        }

        try {
            await apiRequest(`/replies/${replyId}`, {
                method: "DELETE",
            });

            await loadSelectedGroupPosts();
            showToast("Reply deleted.");
        } catch (error) {
            showToast(error.message, "error");
        }
    }
});







/* Profile */

async function loadProfile() {
    try {
        const profile = await apiRequest("/users/me/profile");
        state.currentUser = profile.user;

        sessionStorage.setItem(
            "studyfinderUser",
            JSON.stringify(state.currentUser),
        );

        updateUserHeader();
        renderProfile(profile);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function renderProfile(profile) {
    const user = profile.user;
    const stats = profile.stats;

    document.querySelector("#profile-initials").textContent =
        getInitials(user.display_name);
    document.querySelector("#profile-name").textContent =
        user.display_name;
    document.querySelector("#profile-email").textContent =
        user.email;
    document.querySelector("#profile-major").textContent =
        user.major || "Major not provided";
    document.querySelector("#profile-school-year").textContent =
        user.school_year || "School year not provided";

    document.querySelector("#profile-created-count").textContent =
        stats.groups_created;
    document.querySelector("#profile-joined-count").textContent =
        stats.groups_joined;
    document.querySelector("#profile-session-count").textContent =
        stats.upcoming_sessions;
    document.querySelector("#profile-post-count").textContent =
        stats.discussion_posts;

    document.querySelector("#profile-display-name").value =
        user.display_name;
    document.querySelector("#profile-email-input").value =
        user.email;
    document.querySelector("#profile-major-input").value =
        user.major || "";
    document.querySelector("#profile-year-input").value =
        user.school_year || "";
}

document
    .querySelector("#profile-form")
    .addEventListener("submit", async (event) => {
        event.preventDefault();

        const profileData = {
            display_name: document
                .querySelector("#profile-display-name")
                .value
                .trim(),
            major: optionalValue("#profile-major-input"),
            school_year: optionalValue("#profile-year-input"),
        };

        const message = document.querySelector("#profile-message");

        try {
            state.currentUser = await apiRequest("/users/me", {
                method: "PUT",
                body: JSON.stringify(profileData),
            });

            sessionStorage.setItem(
                "studyfinderUser",
                JSON.stringify(state.currentUser),
            );

            updateUserHeader();
            await loadProfile();
            setMessage(message, "Profile updated.", "success");
        } catch (error) {
            setMessage(message, error.message, "error");
        }
    });

/* Dialogs */

document
    .querySelectorAll("[data-close-dialog]")
    .forEach((button) => {
        button.addEventListener("click", () => {
            document
                .querySelector(`#${button.dataset.closeDialog}`)
                .close();
        });
    });

/* Utilities */

function optionalValue(selector) {
    const value = document.querySelector(selector).value.trim();
    return value || null;
}

function setMessage(element, message, type = "") {
    element.textContent = message;
    element.classList.remove("message-success", "message-error");

    if (type === "success") {
        element.classList.add("message-success");
    } else if (type === "error") {
        element.classList.add("message-error");
    }
}

function showToast(message, type = "success") {
    clearTimeout(toastTimer);

    toast.textContent = message;
    toast.classList.remove("hidden", "toast-error");

    if (type === "error") {
        toast.classList.add("toast-error");
    }

    toastTimer = setTimeout(() => {
        toast.classList.add("hidden");
    }, 3500);
}

function emptyState(message) {
    return `
        <div class="empty-state">
            <p>${escapeHTML(message)}</p>
        </div>
    `;
}

function getInitials(name) {
    return String(name)
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part.charAt(0))
        .join("")
        .toUpperCase();
}

function getFirstName(name) {
    return String(name).trim().split(/\s+/)[0];
}

function getDayPeriod() {
    const hour = new Date().getHours();

    if (hour < 12) {
        return "morning";
    }

    if (hour < 18) {
        return "afternoon";
    }

    return "evening";
}

function formatDateTime(value) {
    const date = new Date(value);

    return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
    }).format(date);
}

function toDateTimeLocal(value) {
    const date = new Date(value);
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60_000);

    return localDate.toISOString().slice(0, 16);
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHTML(value).replaceAll("`", "&#096;");
}

/* Restore login */

async function initializeApplication() {
    const savedUser = sessionStorage.getItem("studyfinderUser");

    if (!state.token || !savedUser) {
        showAuthentication("login");
        return;
    }

    try {
        state.currentUser = JSON.parse(savedUser);
        await startApplication();
    } catch {
        clearStoredLogin();
        showAuthentication("login");
    }
}

initializeApplication();