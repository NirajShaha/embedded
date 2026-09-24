# Admin Panel - UI Flow & Architecture

## 🎯 User Journey Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER AUTHENTICATION FLOW                     │
└─────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  App Starts  │
                              └──────┬───────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │   Check localStorage for       │
                    │   user & JWT token             │
                    └────────────┬───────────────────┘
                                 │
                        ┌────────┴────────┐
                        │                 │
                       NO                YES
                        │                 │
                        ▼                 ▼
                  ┌──────────────┐  ┌──────────────┐
                  │  Login Page  │  │  Redirect to │
                  │              │  │  Dashboard   │
                  └──────┬───────┘  └──────┬───────┘
                         │                 │
              Username + Password          │
                    Submit                 │
                         │                 │
                         ▼                 │
              ┌──────────────────┐         │
              │ POST /auth/login │         │
              │ (Backend)        │         │
              └────────┬─────────┘         │
                       │                   │
              Return: JWT + User Info      │
                       │                   │
                       └───────┬───────────┘
                               │
                        ┌──────▼──────┐
                        │  Dashboard  │
                        │ (All Users) │
                        └──────┬──────┘
                               │
                    ┌──────────┴──────────┐
                   YES                    NO
                    │                      │
              Is User ADMIN?              Regular
                    │                    User View
                    │                    (Read Only)
                    ▼
            ┌─────────────────┐
            │  Admin Panel    │
            │  (Sidebar Link) │
            └────────┬────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
    ┌──────────────┐  ┌──────────────────────┐
    │   Dashboard  │  │ Test Case Management │
    │   (Stats)    │  │ (Create/Edit/Delete) │
    └──────────────┘  └──────────────────────┘
```

## 📱 Page Structure

### 1️⃣ **Login Page** (`/login`)

```
┌─────────────────────────────────────────┐
│                                         │
│     🔐 Embedded Config                 │
│     Security Testing Platform          │
│                                         │
│     Username: [ _________________ ]    │
│     Password: [ _________________ ]    │
│                                         │
│         [ Sign In ]                     │
│                                         │
│     Demo Credentials:                   │
│     Admin: admin / password             │
│     User: user / password               │
│                                         │
└─────────────────────────────────────────┘
```

### 2️⃣ **Dashboard** (`/`) - All Users

```
┌─────────────────────────────────────────────────────────┐
│  📍 Sidebar                    Header                   │
│  ├─ Dashboard (active)   Signed in as: alex  🔋 (ADMIN)│
│  ├─ [Admin Panel] ✨               [Logout]            │
│  └─ Current Project                                     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Dashboard                                         │ │
│  │ Main workspace                                    │ │
│  │                                                   │ │
│  │ ┌──────────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │ │ 42 Projects  │ │ 5 Users  │ │ 3 Test Cases│  │ │
│  │ └──────────────┘ └──────────┘ └──────────────┘  │ │
│  │                                                   │ │
│  │ [+ Create Project]                                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3️⃣ **Admin Dashboard** (`/admin`) - Admin Only

```
┌──────────────────────────────────────────────────────────┐
│  📍 Sidebar                                              │
│  ├─ Dashboard                                            │
│  ├─ Admin Panel (active) ✨                             │
│  └─ Current Project                                     │
│                                                          │
│  Admin Dashboard         🔐 ADMIN  [Logout]             │
│  Welcome back, admin                                     │
│                                                          │
│  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐      │
│  │42 Test Cases│ │5 Users   │ │3 Recent Updates  │      │
│  └─────────────┘ └──────────┘ └──────────────────┘      │
│                                                          │
│  Admin Actions                                           │
│  ┌────────────────────────────────────────────────┐    │
│  │ ✓ Test Case Management                         │    │
│  │   Create, edit, and delete test cases         │    │
│  │                                                │    │
│  │ 👥 User Management (Coming Soon)              │    │
│  │                                                │    │
│  │ ⚙️ System Settings (Coming Soon)              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ℹ️ As admin, you have full control over test cases    │
│     • Create new test cases                             │
│     • Edit existing test cases                          │
│     • Delete test cases permanently                     │
│     • View audit history                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4️⃣ **Test Case Management** (`/admin/test-cases`) - Admin Only

```
┌────────────────────────────────────────────────────────────┐
│  ⬅ Test Case Management        [+ New Test Case]          │
│  Create, edit, and delete test cases      🔐 Admin Only    │
│                                                             │
│  All Test Cases (42)                                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │Action/Test│ Category  │Objective │ Severity│Created │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │Test the a…│ Auth      │Authz     │ High   │1 day ago│ │
│  │           │           │          │        │ [✎][🗑]  │
│  ├──────────────────────────────────────────────────────┤ │
│  │Verify CAN…│ Protocol  │Protocol  │ Medium │2 days… │ │
│  │           │           │          │        │ [✎][🗑]  │
│  ├──────────────────────────────────────────────────────┤ │
│  │...                                                     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└────────────────────────────────────────────────────────────┘

When clicking [+ New Test Case] or [✎ Edit]:

┌────────────────────────────────────────────────────────┐
│  Create New Test Case                          [×]    │
│  Create a new security test case with all fields      │
│                                                        │
│  REQUIRED FIELDS                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Action/Test Case *                               │ │
│  │ [ _________________________________ ]            │ │
│  │                                                  │ │
│  │ Category *        │ Objective *                 │ │
│  │ [ Select ]        │ [ Select ]                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  RELATED RESOURCES (Optional)                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Protocol          │ Attack Vector               │ │
│  │ [ Select ]        │ [ Select ]                  │ │
│  │                                                  │ │
│  │ Test Type         │ Severity                    │ │
│  │ [ Select ]        │ [ Select ]                  │ │
│  │                                                  │ │
│  │ Threat            │                             │ │
│  │ [ Select ]        │ [ Select ]                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  TEST DETAILS & ANALYSIS                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Description                                      │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ Attack Path                                      │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ Test Steps                                       │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ Expected Output                                  │ │
│  │ [ ___________________________ ]                  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  RISK & FEASIBILITY ANALYSIS                           │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Attack Feasibility                               │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ CIA Impact                                       │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ Safety Impact                                    │ │
│  │ [ ___________________________ ]                  │ │
│  │                                                  │ │
│  │ Automation Possible  [ Yes / No / Partial ]     │ │
│  │                                                  │ │
│  │ Source Scope Status  [ _________________ ]      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  [ Create Test Case ]                                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## 🔐 Access Control Rules

| Page                | Normal User | Admin | Login Required |
| ------------------- | ----------- | ----- | -------------- |
| `/login`            | ✅          | ✅    | No             |
| `/` (Dashboard)     | ✅          | ✅    | Yes            |
| `/projects/*`       | ✅          | ✅    | Yes            |
| `/admin`            | ❌          | ✅    | Yes            |
| `/admin/test-cases` | ❌          | ✅    | Yes            |

## 🔄 Component Hierarchy

```
<RootLayout>
  └─ <Providers>
      └─ <AuthProvider>
          └─ <AuthLayout>
              ├─ <Login> (if not authenticated)
              └─ <SidebarProvider>
                  ├─ <AppSidebar>
                  │   ├─ Workspace Links
                  │   ├─ [Admin Panel] (if isAdmin)
                  │   └─ Current Project
                  └─ <SidebarInset>
                      ├─ <Header> with user info + logout
                      └─ <main>
                          ├─ <Dashboard> / <Projects> / <Pages>
                          └─ <ProtectedRoute requiredRole="ADMIN">
                              ├─ <AdminDashboard> / /admin
                              └─ <TestCaseManagement> / /admin/test-cases
                                  └─ <TestCaseForm>
```

## 🎨 Key Features

### Authentication

- ✅ JWT token storage in localStorage
- ✅ Auto-persist login on page refresh
- ✅ Automatic redirect to login if no token
- ✅ Logout clears token & redirects

### Authorization

- ✅ Role-based access (ADMIN vs USER)
- ✅ Admin menu only visible to admins
- ✅ Protected routes check role before rendering
- ✅ Access denied message for non-admins

### Test Case Management

- ✅ Table view of all test cases
- ✅ Create new test case (modal form)
- ✅ Edit existing test case
- ✅ Delete with confirmation dialog
- ✅ All fields displayed and editable
- ✅ Grouped form sections (Required, Optional, Analysis)

## 📦 State Management

```
AuthContext
├─ user: { id, username, role }
├─ isLoading: boolean
├─ isAdmin: boolean (derived from user.role)
├─ login(username, password)
└─ logout()

React Query (TanStack Query)
├─ Test Cases queries
├─ Dropdown options (categories, objectives, etc.)
├─ Admin statistics
└─ Auto-refetch & caching
```

## ✅ What's Ready (Frontend)

- [x] Auth context & hooks
- [x] Login page
- [x] Protected routes
- [x] Admin dashboard
- [x] Test case management UI
- [x] Sidebar with admin menu
- [x] Responsive design
- [x] Dark mode support

## ⏳ Next: Backend Implementation

- [ ] Database: users table + audit columns
- [ ] Auth API: login endpoint
- [ ] RBAC: middleware & decorators
- [ ] Test Case API: add role checks
- [ ] Seed data: default admin/user accounts
