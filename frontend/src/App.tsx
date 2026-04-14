import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { PrivateRoute } from './components/PrivateRoute'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { PropertyListPage } from './pages/PropertyListPage'
import { PropertyDetailPage } from './pages/PropertyDetailPage'
import { PropertyCreatePage } from './pages/PropertyCreatePage'
import { PropertyEditPage } from './pages/PropertyEditPage'
import { MyPropertiesPage } from './pages/MyPropertiesPage'
import { ProfilePage } from './pages/ProfilePage'
import { UsersPage } from './pages/UsersPage'
import { AIChatPage } from './pages/AIChatPage'
import { AISearchPage } from './pages/AISearchPage'
import { PropertyExplainPage } from './pages/PropertyExplainPage'
import { ComparePage } from './pages/ComparePage'
import { FavoritesPage } from './pages/FavoritesPage'
import { NotFoundPage } from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<Layout />}>
          <Route path="/" element={<PropertyListPage />} />
          <Route path="/properties" element={<PropertyListPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />

          <Route
            path="/properties/create"
            element={
              <PrivateRoute>
                <PropertyCreatePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/properties/:id/edit"
            element={
              <PrivateRoute>
                <PropertyEditPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/properties/:id/explain"
            element={
              <PrivateRoute>
                <PropertyExplainPage />
              </PrivateRoute>
            }
          />
          <Route path="/properties/:id" element={<PropertyDetailPage />} />
          <Route
            path="/my-properties"
            element={
              <PrivateRoute>
                <MyPropertiesPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <ProfilePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/users"
            element={
              <PrivateRoute>
                <UsersPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/ai/chat"
            element={
              <PrivateRoute>
                <AIChatPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/ai/search"
            element={
              <PrivateRoute>
                <AISearchPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/compare"
            element={
              <PrivateRoute>
                <ComparePage />
              </PrivateRoute>
            }
          />

          <Route path="/home" element={<Navigate to="/" replace />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
