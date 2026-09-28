import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowUpLeft, ChevronLeft, ChevronRight, Maximize2, Minimize2, Pause, Play, Sparkles, CirclePause } from 'lucide-react'
import { Icon } from './components'
import { fa } from './utils'
import { chapters, Cover, Challenge, Service, OperationalDay, Economics, Pilot, Future } from './StrategyScenes'
import './presentation.css'
const titles=['گذار هوشمند به آینده','قدرت مهندسی مپنا','چالش‌های سوخت فسیلی','انتخاب بخش بازار','چالش‌های ناوگان لجستیک','راهکار یکپارچه مپنا','بوم کسب‌وکار','مقایسه هزینه ناوگان','توجیه اقتصادی','پلتفرم موتورسیکلت','پایلوت عملیاتی ماهکس','پایش و داشبورد','افق توسعه','مسیر آینده']
export default function Presentation() {
  const [chapter, setChapter] = useState(0)
  const [mode, setMode] = useState<'story'|'slides'>('story')
  const [slide, setSlide] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [motion, setMotion] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [fullscreen, setFullscreen] = useState(false)
  const [message, setMessage] = useState('')
  const root = useRef<HTMLDivElement>(null)
  const stage = useRef<HTMLDivElement>(null)
  const frame = useRef<number | null>(null)
  const current = mode === 'story' ? chapter : slide
  const total = mode === 'story' ? chapters.length : titles.length
  const go = useCallback((next: number) => {
    const bounded = Math.max(0, Math.min(total - 1, next))
    if (mode === 'story') setChapter(bounded); else setSlide(bounded)
    if (bounded === total - 1) setPlaying(false)
  }, [mode, total])
  const showDocument = useCallback(() => {setSlide(chapters[chapter].slide);setMode('slides');setPlaying(false)}, [chapter])
  useEffect(() => {
    const keyboard = (event: KeyboardEvent) => {
      const target = event.target
      if (!(target instanceof HTMLElement) || (target !== document.body && !root.current?.contains(target))) return
      if (target.matches('input,select,textarea,[contenteditable="true"]')) return
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {event.preventDefault();go(current + (event.key === 'ArrowLeft' ? 1 : -1))}
      if (event.key === 'Home') {event.preventDefault();go(0)}
      if (event.key === 'End') {event.preventDefault();go(total - 1)}
    }
    window.addEventListener('keydown', keyboard)
    return () => window.removeEventListener('keydown', keyboard)
  }, [current, go, total])
  useEffect(() => {
    if (!playing || document.hidden) return
    const timer = window.setTimeout(() => go(current + 1), 15000)
    return () => window.clearTimeout(timer)
  }, [playing, current, go])
  useEffect(() => {
    const changed = () => setFullscreen(document.fullscreenElement === root.current)
    const hidden = () => {if (document.hidden) setPlaying(false)}
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    const preference = () => {setMotion(!reduced.matches);if (reduced.matches) setPlaying(false)}
    document.addEventListener('fullscreenchange', changed)
    document.addEventListener('visibilitychange', hidden)
    reduced.addEventListener('change', preference)
    return () => {document.removeEventListener('fullscreenchange', changed);document.removeEventListener('visibilitychange', hidden);reduced.removeEventListener('change', preference);if (frame.current !== null) cancelAnimationFrame(frame.current)}
  }, [])
  const toggleFullscreen = async () => {
    try {if (document.fullscreenElement) await document.exitFullscreen();else await root.current?.requestFullscreen();setMessage('')} catch {setMessage('نمایش تمام‌صفحه در این مرورگر در دسترس نیست.')}
  }
  const parallax = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!motion || event.pointerType !== 'mouse') return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = ((event.clientX - rect.left) / rect.width - .5) * 12
    const y = ((event.clientY - rect.top) / rect.height - .5) * 8
    if (frame.current !== null) cancelAnimationFrame(frame.current)
    frame.current = requestAnimationFrame(() => {stage.current?.style.setProperty('--pointer-x', x + 'px');stage.current?.style.setProperty('--pointer-y', y + 'px')})
  }
  return <div className={'strategy-experience ' + (motion ? 'motion-on' : 'motion-off')} ref={root} aria-label="ارائهٔ تعاملی راهبرد ناوگان برقی">
    <header className="story-topbar"><div className="story-wordmark"><span><Icon name="Zap" size={22}/></span><div><b>حرکت به سوی فردا</b><small dir="ltr">MAPNA · MAHAX · TOSAN</small></div></div><div className="story-view-switch" aria-label="نوع ارائه"><button className={mode === 'story' ? 'active' : ''} aria-pressed={mode === 'story'} onClick={() => {setMode('story');setPlaying(false)}}><Sparkles size={15}/>روایت تعاملی</button><button className={mode === 'slides' ? 'active' : ''} aria-pressed={mode === 'slides'} onClick={() => {setMode('slides');setPlaying(false)}}><Icon name="FileText" size={15}/>اسلایدهای اصلی</button></div><div className="story-tools"><button className="story-tool" aria-label={motion ? 'خاموش کردن حرکت‌ها' : 'روشن کردن حرکت‌ها'} title={motion ? 'خاموش کردن حرکت‌ها' : 'روشن کردن حرکت‌ها'} aria-pressed={motion} onClick={() => {setMotion(!motion);setPlaying(false)}}>{motion ? <Sparkles size={17}/> : <CirclePause size={17}/>}</button><button className="story-tool" onClick={toggleFullscreen} aria-label={fullscreen ? 'خروج از تمام‌صفحه' : 'نمایش تمام‌صفحه'} title={fullscreen ? 'خروج از تمام‌صفحه' : 'نمایش تمام‌صفحه'}>{fullscreen ? <Minimize2 size={18}/> : <Maximize2 size={18}/>}</button></div></header>
    {message && <p className="story-message" role="status">{message}</p>}
    {mode === 'story' ? <>
      <div className="story-stage" ref={stage} onPointerMove={parallax} onPointerLeave={() => {if(frame.current !== null)cancelAnimationFrame(frame.current);stage.current?.style.setProperty('--pointer-x','0px');stage.current?.style.setProperty('--pointer-y','0px')}}><div key={chapter} className="story-scene">{chapter === 0 ? <Cover onNext={() => go(1)}/> : chapter === 1 ? <Challenge/> : chapter === 2 ? <Service/> : chapter === 3 ? <OperationalDay/> : chapter === 4 ? <Economics/> : chapter === 5 ? <Pilot/> : <Future onRestart={() => go(0)} onDocument={showDocument}/>}</div><div className="story-stage-footer"><span dir="ltr"><b>{String(chapter + 1).padStart(2,'0')}</b><i/>{chapters[chapter].en}</span><button onClick={showDocument}>مستند این فصل<ArrowUpLeft size={13}/></button></div></div>
      <nav className="story-chapters" aria-label="فصل‌های ارائه">{chapters.map((item, i) => <button key={item.title} onClick={() => go(i)} aria-current={chapter === i ? 'step' : undefined} className={chapter === i ? 'active' : ''}><span className="story-chapter-index">{fa(i + 1).padStart(2,'۰')}</span><Icon name={item.icon} size={17}/><b>{item.title}</b>{chapter === i && <span className={'story-chapter-progress ' + (playing ? 'is-playing' : '')} key={String(playing)}/>}</button>)}</nav>
    </> : <section className="story-document"><div className="presentation-toolbar"><div><b>{titles[slide]}</b><small>اسلاید {fa(slide + 1)} از {fa(titles.length)} · فایل اصلی ارائهٔ مپنا</small></div><span className="story-document-tag"><Icon name="FileText" size={15}/>نسخهٔ مرجع</span></div><img className="slide-image" src={`/media/strategy-${String(slide + 1).padStart(2,'0')}.jpg`} alt={titles[slide]}/><div className="slide-thumbs">{titles.map((title, i) => <button key={title} className={slide === i ? 'active' : ''} onClick={() => go(i)} aria-label={'اسلاید ' + (i + 1) + ' ' + title} aria-current={slide === i ? 'true' : undefined}><img loading="lazy" src={`/media/strategy-${String(i + 1).padStart(2,'0')}.jpg`} alt=""/><span>{fa(i + 1)}</span></button>)}</div></section>}
    <footer className="story-controls"><div className="story-navigation"><button className="story-tool" onClick={() => go(current - 1)} disabled={current === 0} aria-label={mode === 'story' ? 'فصل قبل' : 'اسلاید قبل'}><ChevronRight size={19}/></button><span dir="ltr" aria-live="polite" aria-atomic="true">{fa(current + 1)} <i>/</i> {fa(total)}</span><button className="story-tool" onClick={() => go(current + 1)} disabled={current === total - 1} aria-label={mode === 'story' ? 'فصل بعد' : 'اسلاید بعد'}><ChevronLeft size={19}/></button><span className="story-control-divider"/><button className={'story-autoplay ' + (playing ? 'active' : '')} aria-label={playing ? 'توقف پخش خودکار' : 'شروع پخش خودکار'} onClick={() => {if (!playing && current === total - 1) go(0);setPlaying(!playing)}}>{playing ? <Pause size={15}/> : <Play size={15}/>}<span>{playing ? 'توقف پخش' : 'پخش خودکار'}</span></button></div><span className="story-source-note">روایت راهبردی · تصاویر مفهومی<span className="story-keyboard-hint">کلیدهای <ChevronRight size={12}/><ChevronLeft size={12}/> برای مرور</span></span></footer>
  </div>
}
