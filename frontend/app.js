const API_BASE_URL = "";

let currentUser = null;
let displayedGroups = [];
let membersByGroup = new Map();
let notificationTimer;

/* Page elements */

const authenticationView = document.querySelector("#authentication-view");
const applicationView = document.querySelector("#application-view");
const userNavigation = document.querySelector("#user-navigation");
const welcomeUser = document.querySelector("#welcome-user");

const authenticationTitle = document.querySelector("#authentication-title");
const authenticationSwitchButton = document.querySelector(
    "#authentication-switch-button"
);
const switchText = document.querySelector("#switch-text");

const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const searchForm = document.querySelector("#search-form");
const createGroupForm = document.querySelector("#create-group-form");

const loginMessage = document.querySelector("#login-message");
const registerMessage = document.querySelector("#register-message");
const searchMessage = document.querySelector("#search-message");
const createGroupMessage = document.querySelector("#create-group-message");

const searchInput = document.querySelector("#search-input");
const groupResults = document.querySelector("#group-results");
const resultCount = document.querySelector("#result-count");

const createGroupDialog = document.querySelector("#create-group-dialog");
const groupDialog = document.querySelector("#group-dialog");
const groupDetails = document.querySelector("#group-details");

const notification = document.querySelector("#notification");

let registrationMode = false;

/* API helper */

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        },
        ...options
    });

    if (response.status === 204) {
        return null;
    }

    let data;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
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

/* Authentication view */

function switchAuthenticationMode() {
    registrationMode = !registrationMode;

    loginForm.classList.toggle("hidden", registrationMode);
    registerForm.classList.toggle("hidden", !registrationMode);

    loginMessage.textContent = "";
    registerMessage.textContent = "";

    if (registrationMode) {
        authenticationTitle.textContent = "Create an account";
        switchText.textContent = "Already have an account?";
        authenticationSwitchButton.textContent = "Sign in";
    } else {
        authenticationTitle.textContent = "Sign in";
        switchText.textContent = "New to StudyFinder?";
        authenticationSwitchButton.textContent = "Create an account";
    }
}

authenticationSwitchButton.addEventListener(
    "click",
    switchAuthenticationMode
);

/* Registration */

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    setMessage(registerMessage, "Creating your account...");

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
            .value
    };

    try {
        const response = await apiRequest("/auth/register", {
            method: "POST",
            body: JSON.stringify(registrationData)
        });

        const registeredEmail = registrationData.email;

        registerForm.reset();
        switchAuthenticationMode();

        document.querySelector("#login-email").value = registeredEmail;

        setMessage(
            loginMessage,
            response.message || "Account created. You can now sign in.",
            "success"
        );
    } catch (error) {
        setMessage(registerMessage, error.message, "error");
    }
});

/* Login */

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    setMessage(loginMessage, "Signing in...");

    const loginData = {
        email: document
            .querySelector("#login-email")
            .value
            .trim(),

        password: document
            .querySelector("#login-password")
            .value
    };

    try {
        const response = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify(loginData)
        });

        currentUser = response.user;

        sessionStorage.setItem(
            "studyfinderUser",
            JSON.stringify(currentUser)
        );

        loginForm.reset();
        showApplication();
    } catch (error) {
        setMessage(loginMessage, error.message, "error");
    }
});

/* Logout */

document
    .querySelector("#logout-button")
    .addEventListener("click", () => {
        currentUser = null;
        displayedGroups = [];
        membersByGroup.clear();

        sessionStorage.removeItem("studyfinderUser");

        authenticationView.classList.remove("hidden");
        applicationView.classList.add("hidden");
        userNavigation.classList.add("hidden");

        searchInput.value = "";
        loginMessage.textContent = "";
    });

async function showApplication() {
    authenticationView.classList.add("hidden");
    applicationView.classList.remove("hidden");
    userNavigation.classList.remove("hidden");

    welcomeUser.textContent = currentUser.display_name;

    await loadGroups();
}

/* Group searching */

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadGroups(searchInput.value.trim());
});

async function loadGroups(courseCode = "") {
    setMessage(searchMessage, "Loading groups...");

    const query = courseCode
        ? `?course_code=${encodeURIComponent(courseCode)}`
        : "";

    try {
        displayedGroups = await apiRequest(
            `/study-groups/${query}`
        );

        await loadMemberInformation(displayedGroups);

        renderGroups();

        searchMessage.textContent = "";
    } catch (error) {
        setMessage(searchMessage, error.message, "error");
    }
}

async function loadMemberInformation(groups) {
    membersByGroup.clear();

    await Promise.all(
        groups.map(async (group) => {
            try {
                const members = await apiRequest(
                    `/study-groups/${group.id}/members`
                );

                membersByGroup.set(group.id, members);
            } catch {
                membersByGroup.set(group.id, []);
            }
        })
    );
}

/* Display study groups */

function renderGroups() {
    resultCount.textContent =
        `${displayedGroups.length} ` +
        `${displayedGroups.length === 1 ? "group" : "groups"}`;

    if (displayedGroups.length === 0) {
        groupResults.innerHTML = `
            <div class="empty-state">
                <p>No matching study groups were found.</p>
            </div>
        `;

        return;
    }

    groupResults.innerHTML = displayedGroups
        .map((group) => {
            const members = membersByGroup.get(group.id) || [];

            const isMember = members.some(
                (member) => member.user_id === currentUser.id
            );

            const membershipButton = isMember
                ? `
                    <button
                        class="leave-button"
                        data-action="leave"
                        data-group-id="${group.id}"
                        type="button"
                    >
                        Leave
                    </button>
                `
                : `
                    <button
                        class="join-button"
                        data-action="join"
                        data-group-id="${group.id}"
                        type="button"
                    >
                        Join
                    </button>
                `;

            return `
                <article class="group-row">
                    <div>
                        <h3>${escapeHTML(group.group_name)}</h3>

                        <p>
                            ${escapeHTML(
                                group.description ||
                                "No description provided."
                            )}
                        </p>

                        <span class="course-code">
                            ${escapeHTML(group.course_code)}
                        </span>

                        <span class="member-count">
                            ${members.length} of
                            ${group.max_members} members
                        </span>
                    </div>

                    <div class="group-actions">
                        <button
                            data-action="details"
                            data-group-id="${group.id}"
                            type="button"
                        >
                            Details
                        </button>

                        ${membershipButton}
                    </div>
                </article>
            `;
        })
        .join("");
}

groupResults.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");

    if (!button) {
        return;
    }

    const groupId = Number(button.dataset.groupId);
    const action = button.dataset.action;

    if (action === "details") {
        showGroupDetails(groupId);
    }

    if (action === "join") {
        await joinGroup(groupId);
    }

    if (action === "leave") {
        await leaveGroup(groupId);
    }
});

/* Group details */

function showGroupDetails(groupId) {
    const group = displayedGroups.find(
        (item) => item.id === groupId
    );

    if (!group) {
        return;
    }

    const members = membersByGroup.get(groupId) || [];

    const memberList = members.length
        ? `
            <ul>
                ${members
                    .map(
                        (member) => `
                            <li>
                                ${escapeHTML(member.display_name)}
                            </li>
                        `
                    )
                    .join("")}
            </ul>
        `
        : "<p>No members have joined this group yet.</p>";

    groupDetails.innerHTML = `
        <p class="section-label">
            ${escapeHTML(group.course_code)}
        </p>

        <h2>${escapeHTML(group.group_name)}</h2>

        <p>
            ${escapeHTML(
                group.description || "No description provided."
            )}
        </p>

        <p>
            <strong>Status:</strong>
            ${escapeHTML(group.status)}
        </p>

        <p>
            <strong>Capacity:</strong>
            ${members.length} of ${group.max_members}
        </p>

        <h3>Members</h3>

        ${memberList}
    `;

    groupDialog.showModal();
}

/* Join and leave */

async function joinGroup(groupId) {
    try {
        await apiRequest(
            `/study-groups/${groupId}/members/${currentUser.id}`,
            {
                method: "POST"
            }
        );

        await refreshGroupMembers(groupId);
        renderGroups();

        showNotification("You joined the study group.");
    } catch (error) {
        showNotification(error.message);
    }
}

async function leaveGroup(groupId) {
    try {
        await apiRequest(
            `/study-groups/${groupId}/members/${currentUser.id}`,
            {
                method: "DELETE"
            }
        );

        await refreshGroupMembers(groupId);
        renderGroups();

        showNotification("You left the study group.");
    } catch (error) {
        showNotification(error.message);
    }
}

async function refreshGroupMembers(groupId) {
    const members = await apiRequest(
        `/study-groups/${groupId}/members`
    );

    membersByGroup.set(groupId, members);
}

/* Create a group */

function openCreateGroupDialog() {
    createGroupMessage.textContent = "";
    createGroupDialog.showModal();
}

document
    .querySelector("#open-create-group")
    .addEventListener("click", openCreateGroupDialog);

document
    .querySelector("#sidebar-create-button")
    .addEventListener("click", openCreateGroupDialog);

document
    .querySelector("#close-create-group")
    .addEventListener("click", () => {
        createGroupDialog.close();
    });

createGroupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    setMessage(createGroupMessage, "Creating group...");

    const groupData = {
        group_name: document
            .querySelector("#group-name")
            .value
            .trim(),

        course_code: document
            .querySelector("#course-code")
            .value
            .trim(),

        description: document
            .querySelector("#group-description")
            .value
            .trim(),

        creator_user_id: currentUser.id,
        status: "open",
        max_members: 10
    };

    try {
        const createdGroup = await apiRequest(
            "/study-groups/",
            {
                method: "POST",
                body: JSON.stringify(groupData)
            }
        );

        /*
         * The backend records the creator but does not automatically
         * add the creator to the membership table. This request adds
         * the creator as the first member.
         */
        await apiRequest(
            `/study-groups/${createdGroup.id}/members/${currentUser.id}`,
            {
                method: "POST"
            }
        );

        createGroupForm.reset();
        createGroupDialog.close();

        await loadGroups(searchInput.value.trim());

        showNotification("Study group created.");
    } catch (error) {
        setMessage(
            createGroupMessage,
            error.message,
            "error"
        );
    }
});

/* Dialog closing */

document
    .querySelector("#close-group-dialog")
    .addEventListener("click", () => {
        groupDialog.close();
    });

/* Utility functions */

function setMessage(element, message, type = "") {
    element.textContent = message;

    element.classList.remove(
        "message-success",
        "message-error"
    );

    if (type === "success") {
        element.classList.add("message-success");
    }

    if (type === "error") {
        element.classList.add("message-error");
    }
}

function showNotification(message) {
    clearTimeout(notificationTimer);

    notification.textContent = message;
    notification.classList.remove("hidden");

    notificationTimer = setTimeout(() => {
        notification.classList.add("hidden");
    }, 3500);
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

/* Restore the current browser session */

const savedUser = sessionStorage.getItem("studyfinderUser");

if (savedUser) {
    currentUser = JSON.parse(savedUser);
    showApplication();
}