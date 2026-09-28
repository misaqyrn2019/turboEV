import { useState } from 'react'
import { Icon } from './components'
import { fa } from './utils'
const titles=['گذار هوشمند به آینده','قدرت مهندسی مپنا','چالش‌های سوخت فسیلی','انتخاب بخش بازار','چالش‌های ناوگان لجستیک','راهکار یکپارچه مپنا','بوم کسب‌وکار','مقایسه هزینه ناوگان','توجیه اقتصادی','پلتفرم موتورسیکلت','پایلوت عملیاتی ماهکس','پایش و داشبورد','افق توسعه','مسیر آینده']
export default function Presentation(){
  const [page,setPage]=useState(0)
  return <><div className="notice"><Icon name="Presentation"/><p>تصاویر فایل ارائهٔ MAPNA Electric Fleet Strategy؛ اعداد و مدل‌های این ارائه، دادهٔ عملیاتی سامانه محسوب نمی‌شوند.</p></div><section className="card presentation"><div className="presentation-toolbar"><div><b>{titles[page]}</b><small>صفحه {fa(page+1)} از {fa(titles.length)}</small></div><div className="action-row"><button className="icon-button" onClick={()=>setPage(p=>p-1)} disabled={page===0} aria-label="اسلاید قبل"><Icon name="ChevronRight"/></button><button className="icon-button" onClick={()=>setPage(p=>p+1)} disabled={page===13} aria-label="اسلاید بعد"><Icon name="ChevronLeft"/></button></div></div><img className="slide-image" src={`/media/strategy-${String(page+1).padStart(2,'0')}.jpg`} alt={titles[page]}/><div className="slide-thumbs">{titles.map((title,i)=><button key={title} className={page===i?'active':''} onClick={()=>setPage(i)} aria-label={'اسلاید '+(i+1)+' '+title}><img loading="lazy" src={`/media/strategy-${String(i+1).padStart(2,'0')}.jpg`} alt=""/><span>{fa(i+1)}</span></button>)}</div></section></>
}
