
import time, threading, math
from typing import Dict, Optional, Tuple
import cv2
from .detector_service import process_frame
from .logger_service import log_match

class CameraWorker:
    def __init__(self, cam_id:int, name:str, source, display_interval_ms=50, detect_interval_frames=3, reconnect_delay=10, frame_buffer=1):
        self.id=cam_id; self.name=name; self.source=source
        self.display_interval_ms=int(display_interval_ms); self.detect_interval_frames=max(1,int(detect_interval_frames))
        self.reconnect_delay=int(reconnect_delay); self.frame_buffer=max(1,int(frame_buffer))
        self._cap=None; self._thread=None; self._stop=threading.Event()
        self._frame_lock=threading.Lock(); self._last_bgr=None; self._last_anns=[]; self._frame_cnt=0
        self._metrics_lock=threading.Lock(); self._ema_iat=None; self._last_ts=None
        self._attempts=0; self._oks=0; self._win_start=time.time(); self._lat_ms=0.0; self._drop_pct=0.0; self._ema_half_life=0.8

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear(); self._thread=threading.Thread(target=self._loop, daemon=True); self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            if self._thread and self._thread.is_alive(): self._thread.join(timeout=1.0)
        except Exception: pass
        try:
            if self._cap: self._cap.release()
        except Exception: pass

    def _open(self):
        try:
            if isinstance(self.source,(int,str)) and str(self.source).isdigit():
                cap=cv2.VideoCapture(int(self.source))
            else:
                cap=cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            try: cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
            except Exception: pass
            if not cap.isOpened():
                cap.release(); return None
            return cap
        except Exception:
            return None

    def _update_metrics(self, now_ts):
        if (now_ts - self._win_start) >= 1.0:
            at, ok = self._attempts, self._oks
            drop = (float(at-ok)/float(at)*100.0) if at>0 else 100.0
            lat_ms = float(self._ema_iat*1000.0) if self._ema_iat else 0.0
            with self._metrics_lock:
                self._drop_pct=max(0.0,min(100.0,drop)); self._lat_ms=max(0.0,lat_ms)
            self._attempts=0; self._oks=0; self._win_start=now_ts

    def _loop(self):
        while not self._stop.is_set():
            cap=self._open()
            if cap is None: time.sleep(self.reconnect_delay); continue
            self._cap=cap
            while not self._stop.is_set():
                self._attempts+=1
                if not cap.grab(): time.sleep(0.01); continue
                for _ in range(self.frame_buffer-1): cap.grab()
                ret,frame=cap.retrieve()
                if not ret or frame is None: time.sleep(0.01); continue
                self._oks+=1
                now=time.time()
                if self._last_ts is not None:
                    iat=max(1e-3, now-self._last_ts)
                    if self._ema_iat is None: self._ema_iat=iat
                    else:
                        tau=self._ema_half_life/math.log(2.0)
                        alpha=1.0 - math.exp(-iat/max(1e-6,tau))
                        self._ema_iat=(1.0-alpha)*self._ema_iat + alpha*iat
                self._last_ts=now
                with self._frame_lock: self._last_bgr=frame
                self._frame_cnt+=1
                if (self._frame_cnt % self.detect_interval_frames)==0:
                    anns=process_frame(frame); self._last_anns=anns
                    for a in anns:
                        if a.match and a.antispoof_live:
                            try: log_match(self.name, a.name, a.score)
                            except Exception: pass
                self._update_metrics(now)
                time.sleep(self.display_interval_ms/1000.0)
            try: cap.release()
            except Exception: pass
            self._cap=None
            if not self._stop.is_set(): time.sleep(self.reconnect_delay)

    def snapshot_annotated(self):
        with self._frame_lock:
            fr=None if self._last_bgr is None else self._last_bgr.copy()
        if fr is None: return None
        for a in self._last_anns:
            x1,y1,x2,y2=a.bbox
            color=(0,255,0) if (a.match and a.antispoof_live) else ((0,165,255) if a.score>=0.4 else (0,0,255))
            cv2.rectangle(fr,(x1,y1),(x2,y2),color,2)
            label=a.name if a.match else (a.best_name or "")
            if label:
                cv2.putText(fr,f"{label} ({a.score:.2f})",(x1,max(12,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,0.6,color,2)
        return fr

    def metrics(self)->Tuple[float,float]:
        with self._metrics_lock: return self._lat_ms, self._drop_pct

class CameraManager:
    def __init__(self): self._workers: Dict[int, CameraWorker] = {}
    def list(self): return self._workers
    def get(self, cam_id:int)->Optional[CameraWorker]: return self._workers.get(cam_id)
    def ensure(self, cam_id:int, name:str, source, **kw):
        if cam_id in self._workers: self.stop(cam_id)
        w=CameraWorker(cam_id,name,source,**kw); self._workers[cam_id]=w; w.start()
    def stop(self, cam_id:int):
        w=self._workers.get(cam_id)
        if w: w.stop(); del self._workers[cam_id]
    def stop_all(self):
        for cid in list(self._workers.keys()): self.stop(cid)

manager=CameraManager()
