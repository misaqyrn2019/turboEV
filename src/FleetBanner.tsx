import { Icon } from './components'
import './fleet-banner.css'

const copy: Record<string, {title:string;description:string;label:string}> = {
  dashboard: {title:'هر حرکت، یک قدم به آینده.',description:'از آمادگی موتور تا آخرین تحویل؛ جریان عملیات را در یک نگاه ببینید.',label:'مدیریت یکپارچهٔ ناوگان'},
  vehicles: {title:'از اولین خرید تا آخرین مأموریت.',description:'شناسنامه، وضعیت و چرخهٔ خدمت هر موتورسیکلت را یکپارچه مدیریت کنید.',label:'ناوگان در حرکت'},
  fleets: {title:'وسیله‌ها در کنار هم؛ یک خدمت پیوسته.',description:'موتورها، رانندگان و مراکز توزیع را برای یک عملیات هماهنگ کنار هم قرار دهید.',label:'هماهنگی در مقیاس ناوگان'},
  batteries: {title:'انرژی آماده، برای ادامهٔ مسیر.',description:'سلامت، شارژ و چرخهٔ عمر باتری‌ها؛ تصویری روشن از قلب ناوگان برقی.',label:'مدیریت انرژی'},
  charges: {title:'توقفی کوتاه، برای حرکتی پیوسته.',description:'نوبت‌های شارژ و آمادگی باتری را با نیاز عملیات هماهنگ کنید.',label:'جریان انرژی در مرکز'},
}
export default function FleetBanner({kind='dashboard',onExplore}:{kind?:string;onExplore:()=>void}) {
  const content=copy[kind]||copy.dashboard
  const energy=['batteries','charges'].includes(kind)
  return <section className={'fleet-feature '+(energy?'fleet-feature-energy':'')} aria-label={content.label}><div className="fleet-feature-copy"><span className="fleet-feature-kicker"><i/>{content.label}<span dir="ltr">ELECTRIC MOBILITY</span></span><h2>{content.title}</h2><p>{content.description}</p><button onClick={onExplore}>کشف مسیر ناوگان برقی<Icon name="ArrowUpLeft" size={15}/></button></div><div className="fleet-feature-art" aria-hidden="true"><div className="fleet-feature-halo"/><svg className="fleet-feature-road" viewBox="0 0 460 200"><path d="M-40 175C80 190 35 35 190 72S320 160 500 10"/><path d="M-40 195C80 210 35 55 190 92S320 180 500 30"/></svg>{energy&&<img className="fleet-feature-charger" src="/media/presentation/charging-cabinet.webp" alt=""/>}<img className="fleet-feature-bike" src="/media/presentation/motor-electric-side.webp" alt=""/><span className="fleet-feature-symbol"><Icon name={energy?'Battery':'Zap'} size={23}/></span></div></section>
}
