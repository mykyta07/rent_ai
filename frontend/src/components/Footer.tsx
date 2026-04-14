import { Link } from 'react-router-dom'
import { Facebook, Home, Instagram, Linkedin, Twitter } from 'lucide-react'

export function Footer() {
  return (
    <footer className="mt-20 bg-slate-900 text-slate-300">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 md:grid-cols-4">
        <div>
          <Link to="/" className="flex items-center gap-2 text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand">
              <Home className="h-4 w-4" />
            </span>
            <span className="font-display text-lg font-semibold">RentAI</span>
          </Link>
          <p className="mt-4 text-sm leading-relaxed text-slate-400">
            Розумний пошук нерухомості з AI: купівля, оренда та персональні рекомендації.
          </p>
          <div className="mt-4 flex gap-3">
            <a href="#" className="rounded-full bg-white/10 p-2 hover:bg-white/20">
              <Facebook className="h-4 w-4" />
            </a>
            <a href="#" className="rounded-full bg-white/10 p-2 hover:bg-white/20">
              <Instagram className="h-4 w-4" />
            </a>
            <a href="#" className="rounded-full bg-white/10 p-2 hover:bg-white/20">
              <Twitter className="h-4 w-4" />
            </a>
            <a href="#" className="rounded-full bg-white/10 p-2 hover:bg-white/20">
              <Linkedin className="h-4 w-4" />
            </a>
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-white">Швидкі посилання</h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <Link to="/properties?sale_type=sale" className="hover:text-white">
                Купівля
              </Link>
            </li>
            <li>
              <Link to="/properties?sale_type=rent" className="hover:text-white">
                Оренда
              </Link>
            </li>
            <li>
              <Link to="/properties/create" className="hover:text-white">
                Додати оголошення
              </Link>
            </li>
            <li>
              <Link to="/ai/chat" className="hover:text-white">
                AI асистент
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-white">Типи нерухомості</h3>
          <ul className="mt-4 space-y-2 text-sm">
            <li>
              <Link to="/properties?type=apartment" className="hover:text-white">
                Квартири
              </Link>
            </li>
            <li>
              <Link to="/properties?type=house" className="hover:text-white">
                Будинки
              </Link>
            </li>
            <li>
              <Link to="/properties?type=commercial" className="hover:text-white">
                Комерція
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-white">Контакти</h3>
          <p className="mt-4 text-sm leading-relaxed">
            м. Київ, вул. Хрещатик, 1
            <br />
            +380 44 000 00 00
            <br />
            hello@rentai.example
          </p>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs text-slate-500 sm:flex-row">
          <span>© {new Date().getFullYear()} RentAI</span>
          <div className="flex gap-4">
            <a href="#" className="hover:text-slate-300">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-slate-300">
              Terms of Use
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
