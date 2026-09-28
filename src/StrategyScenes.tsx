import { useState } from 'react'
import { ArrowLeft, ArrowUpLeft, Check, ChevronLeft, Expand } from 'lucide-react'
import { Icon } from './components'
import { fa } from './utils'

const media = '/media/presentation/'
export const chapters = [
  { title: 'افق برقی', en: 'THE ELECTRIC SHIFT', icon: 'Leaf', slide: 0 },
  { title: 'مسئلهٔ عملیات', en: 'THE REAL CHALLENGE', icon: 'Activity', slide: 4 },
  { title: 'خدمت یکپارچه', en: 'BEYOND THE VEHICLE', icon: 'Bike', slide: 5 },
  { title: 'یک روز کاری', en: 'A DAY IN MOTION', icon: 'Flag', slide: 11 },
  { title: 'منطق اقتصادی', en: 'THE BIGGER PICTURE', icon: 'ChartNoAxesCombined', slide: 7 },
  { title: 'پایلوت ماهکس', en: 'PROVE IT IN PRACTICE', icon: 'ShieldCheck', slide: 10 },
  { title: 'مسیر آینده', en: 'THE ROAD AHEAD', icon: 'ArrowUpRight', slide: 12 },
]

function ChapterLabel({ index }: { index: number }) {
  return <div className="story-overline"><span className="story-line"/>{chapters[index].title}<span className="story-edition" dir="ltr">CHAPTER / {String(index + 1).padStart(2, '0')}</span></div>
}

export function Cover({ onNext }: { onNext: () => void }) {
  return <div className="story-cover">
    <div className="story-cover-copy"><ChapterLabel index={0}/><h2>آیندهٔ ناوگان،<br/><em>برقی</em> شروع می‌شود.</h2><p>از یک موتورسیکلت، تا یک خدمت قابل اتکا.<br/>روایتی از انرژی، عملیات و مسیر توسعهٔ ناوگان.</p><button className="story-primary" onClick={onNext}>روایت را آغاز کنید<ArrowLeft size={19}/></button><div className="story-partners"><span>مپنا</span><i/>ماهکس<span className="story-cross">×</span>توسن<small>همراه در مسیر تحول</small></div></div>
    <div className="story-cover-visual"><div className="story-city"/><div className="story-orbit orbit-one"/><div className="story-orbit orbit-two"/><span className="story-vertical-label" dir="ltr">ELECTRIC MOBILITY</span><div className="story-bike-shadow"/><img className="story-cover-bike" src={media + 'motor-electric-side.webp'} alt="تصویر مفهومی موتورسیکلت برقی حمل مرسوله" fetchPriority="high"/><div className="story-float-tag tag-energy"><span><Icon name="Zap" size={21}/></span><div><b>انرژی پاک‌تر</b><small>یک انتخاب برای آینده</small></div><i/></div><div className="story-float-tag tag-connected"><span><Icon name="Activity" size={19}/></span><div><b>عملیات پیوسته</b><small>از حرکت، تا تحویل</small></div></div><span className="story-visual-caption">تصویر مفهومی ناوگان برقی</span></div>
  </div>
}

export function Challenge() {
  const [selected, setSelected] = useState(0)
  const items = [
    { title: 'موتور آمادهٔ خدمت است؟', icon: 'Bike', text: 'آمادگی موتور و باتری باید پیش از تخصیص مأموریت مشخص باشد؛ داشتن وسیله، به‌تنهایی تضمین اجرای عملیات نیست.', label: 'آماده‌به‌کاری' },
    { title: 'توقف، چقدر هزینه دارد؟', icon: 'Clock3', text: 'زمان تعمیر، انتظار برای شارژ و جایگزینی وسیله بر کیفیت خدمت اثر می‌گذارند. این زمان‌ها باید ثبت و تحلیل شوند.', label: 'هزینهٔ توقف' },
    { title: 'در رخداد، چه کسی پاسخ‌گوست؟', icon: 'Headset', text: 'از گزارش خرابی تا رفع آن، مسئول رسیدگی و زمان پاسخ باید روشن باشد تا موتور سریع‌تر به خدمت برگردد.', label: 'پاسخ‌گویی' },
  ]
  return <div className="story-challenge"><div className="story-section-copy"><ChapterLabel index={1}/><h2>مقصد، فقط<br/><em>تعویض موتور نیست.</em></h2><p>عملیات لجستیک به یک چیز نیاز دارد:<br/>ناوگانی که بتوان روی آن حساب کرد.</p><div className="story-challenge-tabs" aria-label="مسئله‌های عملیات">{items.map((item, i) => <button aria-pressed={selected === i} className={selected === i ? 'active' : ''} onClick={() => setSelected(i)} key={item.label}><Icon name={item.icon}/>{item.label}<ChevronLeft size={15}/></button>)}</div></div><div className="story-challenge-photo"><img src={media + 'urban-mobility.webp'} alt="تصویر مفهومی موتور برقی در مرکز لجستیک شهری"/><div className="story-photo-shade"/><div className="story-insight"><span className="story-insight-icon"><Icon name={items[selected].icon} size={25}/></span><div key={selected} className="story-detail-enter"><h3>{items[selected].title}</h3><p>{items[selected].text}</p></div><span className="story-insight-number">۰{fa(selected + 1)}</span></div></div></div>
}

const serviceLayers = [
  { icon: 'Bike', title: 'وسیلهٔ مناسب', text: 'موتورسیکلتی متناسب با بار، مسیر و شرایط واقعی مأموریت.', label: 'وسیله' },
  { icon: 'Battery', title: 'باتری و انرژی', text: 'پایش سلامت باتری، برنامهٔ شارژ و تأمین انرژی برای ادامهٔ شیفت.', label: 'انرژی' },
  { icon: 'Settings', title: 'نگهداری پیشگیرانه', text: 'کنترل پیش از شیفت و رسیدگی به خرابی، پیش از تبدیل‌شدن به توقف طولانی.', label: 'نگهداری' },
  { icon: 'ChartNoAxesCombined', title: 'داده و تصمیم', text: 'تصمیم‌گیری بر پایهٔ کارکرد، مصرف انرژی و آمادگی ثبت‌شدهٔ ناوگان.', label: 'داده' },
  { icon: 'Headset', title: 'پشتیبانی پاسخ‌گو', text: 'مسئول مشخص، مسیر روشن رسیدگی و پایش زمان بازگشت به سرویس.', label: 'پشتیبانی' },
]
export function Service() {
  const [selected, setSelected] = useState(0)
  return <div className="story-service"><div className="story-section-copy"><ChapterLabel index={2}/><h2>یک موتور.<br/><em>یک زنجیرهٔ خدمت.</em></h2><p>ارزش واقعی، در کنار هم قرار گرفتن<br/>وسیله، انرژی و پشتیبانی ساخته می‌شود.</p><div className="story-service-detail story-detail-enter" key={selected}><span className="story-square-icon"><Icon name={serviceLayers[selected].icon} size={24}/></span><h3>{serviceLayers[selected].title}</h3><p>{serviceLayers[selected].text}</p></div></div><div className="story-service-map"><svg className="story-connection-lines" viewBox="0 0 600 470" aria-hidden="true"><path d="M300 235L110 85M300 235L490 85M300 235L545 260M300 235L430 405M300 235L155 400"/></svg><div className="story-service-ring"/><img className="story-service-bike" src={media + 'motor-electric-side.webp'} alt="موتور برقی در مرکز زنجیرهٔ خدمت"/>{serviceLayers.map((item, i) => <button key={item.label} className={'story-service-node node-' + i + (selected === i ? ' active' : '')} onClick={() => setSelected(i)} aria-pressed={selected === i}><span><Icon name={item.icon} size={23}/></span><b>{item.label}</b></button>)}<small className="story-map-hint">هر بخش را انتخاب کنید<Expand size={13}/></small></div></div>
}

const daySteps = [
  { time: 'پیش از حرکت', title: 'آماده برای یک روز تازه', description: 'کنترل موتور و باتری، تأیید ایمنی و تخصیص راننده؛ هر مأموریت از آمادگی شروع می‌شود.', icon: 'ClipboardCheck', label: 'کنترل و تحویل' },
  { time: 'در طول شیفت', title: 'هر مسیر، یک مأموریت روشن', description: 'تخصیص مأموریت، ثبت وضعیت و مدیریت تأخیرها؛ تصویری روشن از جریان عملیات.', icon: 'Flag', label: 'اجرای مأموریت' },
  { time: 'بین مأموریت‌ها', title: 'انرژی برای ادامهٔ مسیر', description: 'هماهنگی نوبت شارژ با نیاز شیفت و وضعیت باتری؛ زمان توقف هم بخشی از برنامه است.', icon: 'Zap', label: 'شارژ و آماده‌سازی' },
  { time: 'پایان شیفت', title: 'تجربهٔ امروز، تصمیم فردا', description: 'ثبت کارکرد، انرژی و رخدادها؛ بازبینی عملکرد برای یک روز بهتر.', icon: 'NotebookPen', label: 'ثبت و بازبینی' },
]
export function OperationalDay() {
  const [step, setStep] = useState(0)
  return <div className="story-day"><div className="story-day-heading"><div><ChapterLabel index={3}/><h2>یک روز کاری،<br/><em>با جریان پیوستهٔ خدمت.</em></h2></div><p>از اولین کنترل تا آخرین گزارش؛<br/>هر مرحله، ادامهٔ مرحلهٔ قبل است.</p></div><div className={'story-road-scene day-step-' + step}><div className="story-road-sky"/><div className="story-road"><i/><i/><i/><i/><i/><i/><i/></div><div className="story-road-progress" style={{width: `${17 + step * 23}%`}}/><div className="story-road-bike" style={{right: `${7 + step * 22}%`}}><img src={media + 'motor-electric-side.webp'} alt="موتور برقی در مسیر مراحل یک شیفت"/>{step === 2 && <span className="story-charge-bolt"><Icon name="Zap" size={26}/></span>}</div><div className="story-road-station"><img src={media + 'charging-cabinet.webp'} alt="تصویر مفهومی کابین شارژ"/></div><span className="story-road-note">نمای مفهومی گردش کار</span></div><div className="story-day-steps">{daySteps.map((item, i) => <button key={item.title} onClick={() => setStep(i)} className={step === i ? 'active' : ''} aria-pressed={step === i}><span className="story-step-index">{i < step ? <Check size={17}/> : fa(i + 1)}</span><div><small>{item.time}</small><b>{item.label}</b></div><Icon name={item.icon} size={19}/></button>)}</div><div className="story-day-detail story-detail-enter" key={step}><b>{daySteps[step].title}</b><p>{daySteps[step].description}</p></div></div>
}

const costs = [
  { title: 'سرمایه‌گذاری', icon: 'Bike', text: 'موتورسیکلت، باتری و زیرساخت اولیه؛ نقطهٔ شروع محاسبه.', tag: 'شروع مسیر' },
  { title: 'انرژی', icon: 'Zap', text: 'مصرف واقعی در مسیر و تعرفهٔ انرژی؛ متناسب با الگوی بهره‌برداری.', tag: 'هر مأموریت' },
  { title: 'نگهداری', icon: 'Settings', text: 'سرویس، قطعات و چرخهٔ عمر باتری؛ در طول استفاده از ناوگان.', tag: 'در طول عمر' },
  { title: 'توقف عملیات', icon: 'Clock3', text: 'زمان خارج از سرویس و مأموریت‌های ازدست‌رفته؛ هزینه‌ای که باید دیده شود.', tag: 'هزینهٔ پنهان' },
]
export function Economics() {
  const [selected, setSelected] = useState(0)
  return <div className="story-economics"><div className="story-section-copy"><ChapterLabel index={4}/><h2>قیمت خرید،<br/><em>تمام داستان نیست.</em></h2><p>ناوگان را در طول عمرش بسنجیم؛<br/>از اولین سرمایه‌گذاری تا هر روز بهره‌برداری.</p><div className="story-cost-summary"><span dir="ltr">TOTAL COST OF OWNERSHIP</span><h3>هزینهٔ کل مالکیت</h3><p>مبنایی برای مقایسهٔ سناریوها،<br/>با دادهٔ واقعی مسیر و عملیات.</p><div className="story-cost-rule"/><small>ارزش باقیمانده نیز در محاسبهٔ نهایی لحاظ می‌شود.</small></div></div><div className="story-cost-board"><div className="story-board-label"><span className="story-live-dot"/>چهار بخش برای یک تصویر کامل<span dir="ltr">TCO</span></div><div className="story-cost-grid">{costs.map((item, i) => <button key={item.title} className={'story-cost-card ' + (selected === i ? 'active' : '')} onClick={() => setSelected(i)} aria-pressed={selected === i}><span className="story-cost-number" dir="ltr">0{i + 1}</span><span className="story-cost-icon"><Icon name={item.icon} size={27}/></span><h3>{item.title}</h3><small>{item.tag}</small><ArrowUpLeft size={17}/></button>)}</div><div className="story-cost-explanation story-detail-enter" key={selected}><Icon name={costs[selected].icon} size={20}/><p>{costs[selected].text}</p></div><div className="story-cost-footer"><Icon name="CircleHelp" size={16}/><span>مقایسهٔ سناریوهای عددی در اسلایدهای اصلی ارائه</span></div></div></div>
}

const gates = [
  { title: 'آمادگی فنی', icon: 'ShieldCheck', text: 'تأیید ایمنی، تناسب موتور و باتری و مسیر رسیدگی به خرابی.' },
  { title: 'آمادگی مرکز', icon: 'PlugZap', text: 'فضای مناسب، تأمین برق و روش اجرایی روشن برای شارژ.' },
  { title: 'آمادگی عملیات', icon: 'Users', text: 'رانندهٔ آموزش‌دیده، شیفت مشخص و مسئول پاسخ‌گو.' },
  { title: 'آمادگی سنجش', icon: 'ChartNoAxesCombined', text: 'خط مبنا، شاخص‌های توافق‌شده و ثبت منظم اطلاعات.' },
]
export function Pilot() {
  const [selected, setSelected] = useState(0)
  const [energy, setEnergy] = useState<'charge'|'swap'>('charge')
  return <div className="story-pilot"><div className="story-section-copy"><ChapterLabel index={5}/><h2>کوچک شروع کنیم.<br/><em>دقیق بسنجیم.</em></h2><p>پایلوت ماهکس، فرصتی برای سنجش خدمت<br/>در شرایط واقعی عملیات است.</p><div className="story-gates">{gates.map((gate, i) => <button key={gate.title} onClick={() => setSelected(i)} className={selected === i ? 'active' : ''} aria-expanded={selected === i}><span><Icon name={gate.icon} size={19}/></span><div><b>{gate.title}</b>{selected === i && <p className="story-detail-enter">{gate.text}</p>}</div><ChevronLeft size={16}/></button>)}</div></div><div className="story-pilot-visual"><div className="story-pilot-label"><Icon name="MapPin" size={16}/><span>مرکز توزیع · سناریوی تأمین انرژی</span></div><div className="story-energy-image" key={energy}><div className="story-energy-aura"/><img className="story-energy-station" src={media + (energy === 'charge' ? 'charging-cabinet.webp' : 'battery-swap-station.webp')} alt={energy === 'charge' ? 'تصویر مفهومی کابین شارژ باتری' : 'تصویر مفهومی ایستگاه تعویض باتری'}/><img className="story-energy-bike" src={media + 'motor-electric-side.webp'} alt="موتور برقی در مرکز تأمین انرژی"/><span className="story-energy-symbol"><Icon name={energy === 'charge' ? 'PlugZap' : 'Battery'} size={25}/></span></div><div className="story-energy-toggle" aria-label="سناریوی انرژی"><button aria-pressed={energy === 'charge'} className={energy === 'charge' ? 'active' : ''} onClick={() => setEnergy('charge')}><Icon name="PlugZap" size={17}/>شارژ در مرکز</button><button aria-pressed={energy === 'swap'} className={energy === 'swap' ? 'active' : ''} onClick={() => setEnergy('swap')}><Icon name="Battery" size={17}/>تعویض باتری</button></div><p className="story-energy-caption">دو گزینه برای بررسی؛ انتخاب نهایی به تأیید فنی و الگوی مأموریت وابسته است.</p></div></div>
}

export function Future({ onRestart, onDocument }: { onRestart: () => void; onDocument: () => void }) {
  return <div className="story-future"><img className="story-future-background" src={media + 'urban-mobility.webp'} alt="چشم‌انداز مفهومی لجستیک شهری برقی"/><div className="story-future-shade"/><div className="story-future-copy"><ChapterLabel index={6}/><h2>آینده، از یک<br/><em>قدم سنجیده آغاز می‌شود.</em></h2><p>اول تجربهٔ قابل اندازه‌گیری.<br/>بعد تصمیم برای توسعه.</p><div className="story-future-actions"><button className="story-primary" onClick={onDocument}>مرور اسلایدهای اصلی<ArrowUpLeft size={18}/></button><button className="story-text-button" onClick={onRestart}><Icon name="RefreshCw" size={16}/>بازگشت به آغاز</button></div></div><div className="story-roadmap">{[['تعریف پایلوت','توافق بر دامنه، مسئولیت و شاخص‌ها'],['اعتبارسنجی خدمت','سنجش عملکرد در عملیات واقعی'],['توسعهٔ مرحله‌ای','مشروط به نتایج و آمادگی زیرساخت']].map(([title, text], i) => <div key={title}><span>{fa(i + 1)}</span><div><h3>{title}</h3><p>{text}</p></div>{i < 2 && <ChevronLeft size={19}/>}</div>)}</div></div>
}
