import { useEffect, useRef, useState } from 'react'
import { ArrowDown, ArrowLeft, ArrowUpLeft, BatteryCharging, Bike, ChevronLeft, MapPin, Moon, Mouse, Pause, Play, Radar, Sun, Zap } from 'lucide-react'
import type { User } from './types'
import { api } from './api'
import { ErrorBox, Icon, Logo } from './components'
import './login.css'

const scenes = [
  { label: 'حرکت', number: '۰۱', title: 'آینده،', accent: 'با شما در حرکت است.', description: 'از اولین حرکت تا آخرین تحویل؛ همهٔ ناوگان در یک مسیر روشن.', icon: Bike, detail: 'هر موتور، یک شناسنامه', text: 'خرید، تخصیص، سرویس و مأموریت؛ تمام مسیر هر موتورسیکلت را در یک‌جا دنبال کنید.' },
  { label: 'انرژی', number: '۰۲', title: 'انرژیِ امروز،', accent: 'حرکتِ فردا.', description: 'باتری آماده. شارژ هماهنگ. یک قدم نزدیک‌تر به عملیات پیوسته.', icon: BatteryCharging, detail: 'انرژی در زمان درست', text: 'وضعیت باتری‌ها، نوبت‌های شارژ و آمادگی مراکز را کنار نیاز عملیات ببینید.' },
  { label: 'مدیریت', number: '۰۳', title: 'یک تصویر روشن،', accent: 'از تمام مسیر.', description: 'موتور، راننده و مأموریت؛ متصل به یک مرکز مدیریت یکپارچه.', icon: Radar, detail: 'از اطلاعات به تصمیم', text: 'مأموریت‌ها، خرابی‌ها و عملکرد مراکز را بررسی کنید و با دید روشن‌تری تصمیم بگیرید.' },
]
const wideQuery = '(min-width: 1000px) and (min-height: 720px)'
const clamp = (value: number) => Math.min(1, Math.max(0, value))

export default function Login({ onLogin, loadError }: { onLogin: (value: { user: User; csrf: string }) => Promise<void>; loadError: string }) {
  const root = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<HTMLElement>(null)
  const scrollFrame = useRef(0)
  const pointerFrame = useRef(0)
  const wheelDistance = useRef(0)
  const [phase, setPhase] = useState(0)
  const [night, setNight] = useState(false)
  const [paused, setPaused] = useState(false)
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [detail, setDetail] = useState<number | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(loadError)
  const motionOff = paused || reduced

  useEffect(() => { setError(loadError) }, [loadError])
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduced(preference.matches)
    preference.addEventListener('change', update)
    return () => preference.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    const wide = window.matchMedia(wideQuery)
    const update = () => {
      cancelAnimationFrame(scrollFrame.current)
      scrollFrame.current = requestAnimationFrame(() => {
        const el = root.current
        if (!el || !wide.matches) return
        const distance = el.offsetHeight - window.innerHeight
        const progress = clamp(-el.getBoundingClientRect().top / Math.max(1, distance))
        el.style.setProperty('--journey', String(progress))
        setPhase(Math.min(2, Math.floor(progress * 3)))
      })
    }
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    wide.addEventListener('change', update)
    update()
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
      wide.removeEventListener('change', update)
      cancelAnimationFrame(scrollFrame.current)
      cancelAnimationFrame(pointerFrame.current)
    }
  }, [])

  useEffect(() => {
    if (motionOff) {
      cancelAnimationFrame(pointerFrame.current)
      root.current?.style.setProperty('--pointer-x', '0')
      root.current?.style.setProperty('--pointer-y', '0')
    }
  }, [motionOff])

  function goTo(index: number) {
    setDetail(null)
    const el = root.current
    if (el && window.matchMedia(wideQuery).matches) {
      const progress = index === 0 ? 0 : (index + 0.35) / 3
      window.scrollTo({ top: window.scrollY + el.getBoundingClientRect().top + (el.offsetHeight - window.innerHeight) * progress, behavior: motionOff ? 'instant' : 'smooth' })
    } else {
      setPhase(index)
      el?.style.setProperty('--journey', String(index / 2))
    }
  }

  function movePointer(event: React.PointerEvent<HTMLElement>) {
    if (motionOff || event.pointerType !== 'mouse') return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
    cancelAnimationFrame(pointerFrame.current)
    pointerFrame.current = requestAnimationFrame(() => {
      root.current?.style.setProperty('--pointer-x', x.toFixed(3))
      root.current?.style.setProperty('--pointer-y', y.toFixed(3))
    })
  }

  function leavePointer() {
    cancelAnimationFrame(pointerFrame.current)
    root.current?.style.setProperty('--pointer-x', '0')
    root.current?.style.setProperty('--pointer-y', '0')
  }

  function compactWheel(event: React.WheelEvent<HTMLElement>) {
    // Native scrolling is never cancelled. Compact layouts also offer buttons.
    if (window.matchMedia(wideQuery).matches || event.ctrlKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return
    wheelDistance.current += event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1)
    if (Math.abs(wheelDistance.current) >= 150) {
      goTo(Math.max(0, Math.min(2, phase + Math.sign(wheelDistance.current))))
      wheelDistance.current = 0
    }
  }

  async function submit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await onLogin(await api<{ user: User; csrf: string }>('/auth/login', 'POST', { username, password }))
      window.scrollTo({ top: 0, behavior: 'instant' })
    } catch (error) {
      setError((error as Error).message)
    } finally { setBusy(false) }
  }

  const current = scenes[phase]
  const selected = detail === null ? null : scenes[detail]

  return <div ref={root} className="login-experience" data-phase={phase} data-night={night} data-motion={motionOff ? 'off' : 'on'}>
    <div className="login-viewport">
      <header className="login-header">
        <Logo dark/>
        <span className="login-header-caption">سامانهٔ هوشمند ناوگان مپنا <i/> از انرژی تا حرکت</span>
        <div className="login-visual-controls">
          <button className="login-control" type="button" aria-label={night ? 'نمای روز' : 'نمای شب'} aria-pressed={night} onClick={() => setNight(!night)}>{night ? <Sun size={19}/> : <Moon size={19}/>}</button>
          <button className="login-control" type="button" disabled={reduced} aria-label={motionOff ? 'فعال کردن حرکت‌ها' : 'توقف حرکت‌ها'} aria-pressed={motionOff} onClick={() => setPaused(!paused)}>{motionOff ? <Play size={18}/> : <Pause size={18}/>}</button>
        </div>
      </header>

      <div className="login-layout">
        <section className="mapna-access" aria-labelledby="login-title">
          <div className="access-card">
            <span className="access-overline"><span/> فضای کاری شما</span>
            <h1 id="login-title">خوش آمدید<span>.</span></h1>
            <p className="access-intro">مدیریت یکپارچهٔ ناوگان، از اینجا شروع می‌شود.</p>
            <form onSubmit={submit} aria-busy={busy}>
              <ErrorBox message={error}/>
              <div className="form-field">
                <label htmlFor="username">نام کاربری</label>
                <div className="input-icon"><Icon name="Users" size={19}/><input id="username" name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} required dir="ltr" placeholder="نام کاربری خود را وارد کنید" value={username} onChange={event => setUsername(event.target.value)}/>{username && <span className="access-field-dot" aria-hidden="true"/>}</div>
              </div>
              <div className="form-field">
                <label htmlFor="password">رمز عبور</label>
                <div className="input-icon"><Icon name="LockKeyhole" size={19}/><input id="password" name="password" autoComplete="current-password" required dir="ltr" type={show ? 'text' : 'password'} placeholder="رمز عبور خود را وارد کنید" value={password} onChange={event => setPassword(event.target.value)}/><button type="button" className="icon-button" aria-label={show ? 'پنهان کردن رمز' : 'نمایش رمز'} aria-pressed={show} onClick={() => setShow(!show)}><Icon name={show ? 'EyeOff' : 'Eye'} size={19}/></button></div>
              </div>
              <button type="submit" className="access-submit" disabled={busy}><span>{busy ? 'در حال ورود…' : 'ورود به سامانه'}</span><span className="access-submit-arrow"><Icon name={busy ? 'LoaderCircle' : 'ArrowLeft'} size={20} className={busy ? 'spin' : ''}/></span></button>
            </form>
            <div className="access-help"><Icon name="ShieldCheck" size={18}/><p>حساب کاربری توسط مدیر سامانه ایجاد می‌شود.</p></div>
          </div>
          <div className="access-note"><span className="access-note-line"/><span>انرژی. حرکت. اطمینان.</span><span className="access-note-line"/></div>
        </section>

        <section ref={sceneRef} className="login-scene" aria-label="سفر تعاملی ناوگان مپنا" onPointerMove={movePointer} onPointerLeave={leavePointer} onWheel={compactWheel}>
          <div className="login-scene-grid" aria-hidden="true"/>
          <div className="login-pointer-glow" aria-hidden="true"/>
          <div className="login-scene-heading" aria-live="polite" aria-atomic="true">
            <div className="login-scene-kicker"><span/> آیندهٔ تحرک برقی <span dir="ltr">MAPNA E-MOBILITY</span></div>
            <h2 key={phase}>{current.title}<br/><em>{current.accent}</em></h2>
            <p>{current.description}</p>
          </div>
          <div className="login-world">
            <div className="login-world-type" aria-hidden="true">{phase === 1 ? 'ENERGY' : phase === 2 ? 'CONNECT' : 'ELECTRIC'}</div>
            <div className="login-orbit login-orbit-one" aria-hidden="true"/>
            <div className="login-orbit login-orbit-two" aria-hidden="true"/>
            <img className="login-city" src="/media/presentation/urban-mobility.webp" alt="" aria-hidden="true"/>
            <svg className="login-road" viewBox="0 0 760 320" fill="none" aria-hidden="true"><path className="login-road-border" d="M-80 265C80 400 220 5 485 170S750 290 850 60"/><path className="login-road-base" d="M-80 265C80 400 220 5 485 170S750 290 850 60"/><path className="login-road-dashes" d="M-80 265C80 400 220 5 485 170S750 290 850 60"/></svg>
            <img className="login-charger" src="/media/presentation/charging-cabinet.webp" alt="" aria-hidden="true"/>
            <div className="login-motor-wrap"><div className="login-motor-shadow"/><img className="login-motor" src="/media/presentation/motor-electric-side.webp" alt="تصویر مفهومی موتورسیکلت برقی مپنا" fetchPriority="high" draggable={false}/></div>
            <div className="login-route-pins" aria-hidden="true"><span><MapPin size={18}/>مرکز توزیع</span><span><MapPin size={18}/>مقصد مأموریت</span></div>
            <button type="button" className="login-floating-card login-energy-card" aria-label="آشنایی با مدیریت انرژی" aria-expanded={detail === 1} onClick={() => setDetail(detail === 1 ? null : 1)}><span className="login-float-icon"><Zap size={21}/></span><span><b>{phase === 1 ? 'جریان انرژی' : 'قدرت حرکت'}</b><small>باتری و زیرساخت شارژ</small></span><ArrowUpLeft size={17}/><span className="login-charge-bars" aria-hidden="true"><i/><i/><i/><i/><i/></span></button>
            <button type="button" className="login-floating-card login-connect-card" aria-label="آشنایی با مدیریت ناوگان" aria-expanded={detail === 2} onClick={() => setDetail(detail === 2 ? null : 2)}><span className="login-float-icon"><Radar size={21}/></span><span><b>همه‌چیز، در ارتباط</b><small>ناوگان · راننده · مأموریت</small></span><i className="login-signal"/></button>
            {selected && <div className="login-detail" role="status"><button type="button" aria-label="بستن توضیحات" onClick={() => setDetail(null)}><Icon name="X" size={17}/></button><b>{selected.detail}</b><p>{selected.text}</p></div>}
          </div>
          <div className="login-scene-bottom">
            <nav className="login-scene-nav" aria-label="صحنه‌های صفحه ورود">{scenes.map((scene, index) => <button type="button" key={scene.label} onClick={() => goTo(index)} aria-current={phase === index ? 'step' : undefined}><span>{scene.number}</span><scene.icon size={17}/><b>{scene.label}</b><ChevronLeft size={14}/></button>)}</nav>
            <span className="login-concept-label">تصویرسازی مفهومی ناوگان برقی</span>
          </div>
        </section>
      </div>

      <footer className="login-footer"><span>مپنا <i/> مدیریت هوشمند ناوگان</span><button type="button" className="login-scroll-cue" onClick={() => goTo(phase === 2 ? 0 : phase + 1)}><Mouse size={19}/><span>{phase === 2 ? 'بازگشت به آغاز سفر' : 'اسکرول کنید؛ مسیر را کشف کنید'}</span><ArrowDown size={15}/></button><span className="login-edition" dir="ltr">ENERGY TO MOBILITY <ArrowLeft size={13}/></span></footer>
      <div className="login-progress-track" aria-hidden="true"><span/></div>
    </div>
  </div>
}
