import React from 'react';
import {AbsoluteFill, OffthreadVideo, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import beats from '../beats.json';

const B = beats.beats as Record<string, number>;
const C = {red: '#E8141C', yellow: '#F0B90B', ice: '#8FDBFF', hot: '#FF7A1A', ink: '#0B1A3F', white: '#FFFFFF', dim: '#9FB2D9'};
const FONT = 'PoppinsXB';

// load the local font before the first frame
const fontHandle = delayRender('font');
const ff = new FontFace(FONT, `url(${staticFile('Poppins-ExtraBold.ttf')})`);
ff.load().then((f) => { (document as any).fonts.add(f); continueRender(fontHandle); });

const useT = () => { const f = useCurrentFrame(); const {fps} = useVideoConfig(); return {f, fps, t: f / fps}; };
// eased 0->1 that starts on a beat (seconds)
const pop = (f: number, fps: number, at: number, damping = 14) => spring({frame: f - Math.round(at * fps), fps, config: {damping, stiffness: 140, mass: 0.8}});
const win = (t: number, a: number, b: number, fade = 0.35) =>
  interpolate(t, [a - fade, a, b, b + fade], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
const draw = (t: number, a: number, len = 0.6) => interpolate(t, [a, a + len], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

// ---- icons (flat vector) ----
const BinanceMark: React.FC<{size: number; color?: string}> = ({size, color = C.yellow}) => (
  <svg width={size} height={size} viewBox="0 0 24 24"><path fill={color} d="M16.624 13.9202l2.7175 2.7154-7.353 7.353-7.353-7.352 2.7175-2.7164 4.6355 4.6595 4.6356-4.6595zm4.6366-4.6366L24 12l-2.7154 2.7164L18.5682 12l2.6924-2.7164zm-9.272.001l2.7163 2.6914-2.7164 2.7174v-.001L9.2721 12l2.7164-2.7154zm-9.2722-.001L5.4088 12l-2.6914 2.6924L0 12l2.7164-2.7164zM11.9885.0115l7.353 7.329-2.7174 2.7154-4.6356-4.6356-4.6355 4.6595-2.7174-2.7154 7.353-7.353z" /></svg>
);
const Person: React.FC<{size: number; color?: string}> = ({size, color = C.white}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><circle cx="50" cy="32" r="20" fill={color} /><path d="M12 96c0-24 17-38 38-38s38 14 38 38z" fill={color} /></svg>
);
const Hacker: React.FC<{size: number}> = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <path d="M50 6c-22 0-34 18-34 40v50h68V46C84 24 72 6 50 6z" fill="#111827" stroke={C.red} strokeWidth="4" />
    <ellipse cx="50" cy="48" rx="20" ry="22" fill="#000" />
    <rect x="36" y="44" width="10" height="5" rx="2" fill={C.red} /><rect x="54" y="44" width="10" height="5" rx="2" fill={C.red} />
  </svg>
);
const Vault: React.FC<{w: number; h: number; color: string; dial?: boolean; children?: React.ReactNode}> = ({w, h, color, dial = false, children}) => (
  <div style={{width: w, height: h, borderRadius: 34, background: color, border: `8px solid ${C.white}`, position: 'relative',
    boxShadow: 'inset 0 -18px 0 rgba(0,0,0,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    {dial && <svg width={w * 0.5} height={w * 0.5} viewBox="0 0 100 100" style={{position: 'absolute', opacity: 0.35}}>
      <circle cx="50" cy="50" r="40" fill="none" stroke={C.ink} strokeWidth="8" />
      {[0, 60, 120].map((a) => <line key={a} x1="50" y1="14" x2="50" y2="86" stroke={C.ink} strokeWidth="7" transform={`rotate(${a} 50 50)`} />)}
    </svg>}
    {children}
  </div>
);
const Snowflake: React.FC<{size: number}> = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">{[0, 60, 120].map((a) => (
    <g key={a} transform={`rotate(${a} 50 50)`} stroke={C.white} strokeWidth="7" strokeLinecap="round">
      <line x1="50" y1="8" x2="50" y2="92" /><line x1="50" y1="22" x2="40" y2="12" /><line x1="50" y1="22" x2="60" y2="12" />
      <line x1="50" y1="78" x2="40" y2="88" /><line x1="50" y1="78" x2="60" y2="88" /></g>))}</svg>
);
const Wifi: React.FC<{size: number; color: string; pulse?: number; slash?: number}> = ({size, color, pulse = 1, slash = 0}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    {[0, 1, 2].map((i) => <path key={i} d={`M${50 - 14 - i * 14} ${70 - 10 - i * 12}a${14 + i * 14} ${14 + i * 14} 0 0 1 ${28 + i * 28} 0`}
      fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" opacity={Math.min(1, Math.max(0.25, pulse * 3 - i))} />)}
    <circle cx="50" cy="74" r="7" fill={color} />
    {slash > 0 && <line x1="14" y1="14" x2={14 + 72 * slash} y2={14 + 72 * slash} stroke={C.red} strokeWidth="10" strokeLinecap="round" />}
  </svg>
);
const PenDrive: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w * 0.42} viewBox="0 0 240 100"><rect x="4" y="16" width="170" height="68" rx="14" fill={C.white} />
    <rect x="174" y="30" width="58" height="40" rx="4" fill={C.dim} /><rect x="190" y="40" width="10" height="8" fill={C.ink} />
    <rect x="208" y="40" width="10" height="8" fill={C.ink} /><rect x="28" y="38" width="90" height="24" rx="6" fill={C.ice} /></svg>
);
const Bank: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w * 0.8} viewBox="0 0 200 160">
    <polygon points="100,6 192,48 8,48" fill={C.white} /><rect x="16" y="52" width="168" height="12" fill={C.white} />
    {[30, 66, 102, 138].map((x) => <rect key={x} x={x} y="70" width="22" height="64" rx="3" fill={C.white} />)}
    <rect x="8" y="138" width="184" height="16" rx="3" fill={C.white} /><circle cx="100" cy="32" r="8" fill={C.yellow} />
  </svg>
);
const Coin: React.FC<{size: number}> = ({size}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><circle cx="50" cy="50" r="44" fill={C.yellow} stroke="#B88A00" strokeWidth="6" />
    <text x="50" y="66" textAnchor="middle" fontFamily={FONT} fontSize="46" fill="#7A5A00">$</text></svg>
);
const Label: React.FC<{text: string; size?: number; color?: string; style?: React.CSSProperties}> = ({text, size = 56, color = C.white, style}) => (
  <div style={{fontFamily: FONT, fontSize: size, color, letterSpacing: -1, textAlign: 'center', lineHeight: 1.05, whiteSpace: 'nowrap', ...style}}>{text}</div>
);
const at = (x: number, y: number, s = 1, o = 1, extra: React.CSSProperties = {}): React.CSSProperties =>
  ({position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) scale(${s})`, opacity: o, ...extra});

// ---- background: the reels' blue blueprint grid ----
const Grid: React.FC = () => (
  <AbsoluteFill style={{background: '#1C3E8C'}}>
    <svg width="1080" height="1920">
      <defs>
        <pattern id="g1" width="27" height="27" patternUnits="userSpaceOnUse"><path d="M27 0H0V27" fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth="1" /></pattern>
        <pattern id="g2" width="135" height="135" patternUnits="userSpaceOnUse"><rect width="135" height="135" fill="url(#g1)" /><path d="M135 0H0V135" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="2" /></pattern>
      </defs>
      <rect width="1080" height="1920" fill="url(#g2)" />
    </svg>
  </AbsoluteFill>
);

export const Explainer: React.FC = () => {
  const {f, fps, t} = useT();
  const P = (k: string, d?: number) => pop(f, fps, B[k], d);
  // phases
  const A = win(t, 0, B.hacker - 0.2), Bp = win(t, B.hacker, B.bank - 0.2), Cp = win(t, B.bank, B.attack - 0.1), Dp = win(t, B.attack, 99, 0.2);
  const shake = t > B.stolen && t < B.stolen + 0.5 ? Math.sin(f * 2.3) * 10 : 0;
  const flash = interpolate(t, [B.attack, B.attack + 0.08, B.attack + 0.5], [0, 0.55, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{transform: `translateX(${shake}px)`}}>
      <Grid />
      {/* header: Binance */}
      <div style={at(330, 230, P('binance'), 1, {display: 'flex', alignItems: 'center', gap: 22})}>
        <BinanceMark size={120} /><Label text="BINANCE" size={104} color={C.yellow} />
      </div>
      {/* presenter in a circle (his lips stay in sync with the voice) */}
      <div style={at(885, 230, P('binance'), 1, {width: 280, height: 280, borderRadius: '50%', overflow: 'hidden', border: `9px solid ${C.white}`})}>
        <OffthreadVideo src={staticFile('pip.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </div>

      {/* ---- A: two wallets ---- */}
      <AbsoluteFill style={{opacity: A}}>
        <div style={at(290, 820, P('cold'))}>
          <Vault w={400} h={470} color="#3FA9E0">
            <div style={{position: 'absolute', top: 60}}><Snowflake size={150} /></div>
            <div style={{position: 'absolute', inset: 0, borderRadius: 26, background: 'rgba(220,245,255,0.55)', opacity: draw(t, B.freeze, 0.8)}} />
            <div style={{position: 'absolute', bottom: 40, opacity: draw(t, B.freeze, 0.5)}}><Label text="FROZEN" size={48} color={C.ink} /></div>
          </Vault>
          <Label text="COLD WALLET" size={62} style={{marginTop: 20}} />
        </div>
        <div style={at(790, 820, P('hot'))}>
          <Vault w={400} h={470} color={C.hot}>
            <div style={{position: 'absolute', top: 40}}><Wifi size={190} color={C.white} pulse={(t - B.internet) % 1.2} /></div>
            <div style={{position: 'absolute', bottom: 46, opacity: draw(t, B.internet, 0.4)}}><Label text="ONLINE" size={52} color={C.white} /></div>
          </Vault>
          <Label text="HOT WALLET" size={62} style={{marginTop: 20}} />
        </div>
        {/* you, me, everyone -> hot wallet */}
        <svg width="1080" height="1920" style={{position: 'absolute', opacity: draw(t, B.users, 0.4)}}>
          {[600, 790, 980].map((x, i) => <line key={i} x1={x - 0} y1={1330} x2={790} y2={1150} stroke={C.white} strokeWidth="6" strokeDasharray="18 14"
            strokeDashoffset={-f * 3} opacity={0.8} />)}
        </svg>
        {[600, 790, 980].map((x, i) => <div key={i} style={at(x, 1390, pop(f, fps, B.users + i * 0.12))}><Person size={110} /></div>)}
        <div style={at(790, 1500, draw(t, B.users, 0.4))}><Label text="You • Me • Everyone" size={44} color={C.white} /></div>
        {/* cold: pen drive, offline */}
        <div style={at(290, 1360, P('pendrive'))}><PenDrive w={300} /><Label text="Like a Pen Drive" size={42} style={{marginTop: 8}} /></div>
        <div style={at(290, 1530, P('offline'))}><div style={{display: 'flex', alignItems: 'center', gap: 10}}>
          <Wifi size={90} color={C.white} slash={draw(t, B.offline + 0.2, 0.4)} /><Label text="OFFLINE" size={48} color={C.white} /></div></div>
      </AbsoluteFill>

      {/* ---- B: not individual accounts -> Binance's own hot wallet ---- */}
      <AbsoluteFill style={{opacity: Bp}}>
        <div style={at(230, 1000, P('hacker'))}><Hacker size={300} /><Label text="HACKERS" size={60} color={C.red} style={{marginTop: 6}} /></div>
        {/* individual account: crossed out on "not" */}
        <div style={at(700, 700, P('individual'), interpolate(t, [B.notTaken, B.notTaken + 0.4], [1, 0.55], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))}>
          <div style={{width: 640, padding: '30px 24px', borderRadius: 30, background: C.white, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative'}}>
            <Person size={160} color="#1C3E8C" />
            <div style={{position: 'relative'}}>
              <Label text="Individual Account" size={58} color={C.ink} />
              <div style={{position: 'absolute', left: -6, top: '50%', height: 12, borderRadius: 6, background: C.red, width: `${draw(t, B.notTaken, 0.35) * 104}%`}} />
            </div>
          </div>
        </div>
        <div style={at(700, 640, pop(f, fps, B.notTaken + 0.15, 10))}>
          <svg width="260" height="260" viewBox="0 0 100 100"><path d="M18 18L82 82M82 18L18 82" stroke={C.red} strokeWidth="13" strokeLinecap="round" /></svg>
        </div>
        {/* Binance's own hot wallet */}
        <div style={at(760, 1310, P('binanceOwn'))}>
          <Vault w={420} h={360} color={C.hot}><div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            <BinanceMark size={150} /><Label text="BINANCE" size={50} color={C.white} style={{marginTop: 8}} /></div></Vault>
          <Label text="Binance HOT WALLET" size={58} color={C.yellow} style={{marginTop: 18}} />
        </div>
        <svg width="1080" height="1920" style={{position: 'absolute'}}>
          <path d="M330 1030 C 470 1140, 520 1260, 545 1300" fill="none" stroke={C.red} strokeWidth="12" strokeLinecap="round"
            strokeDasharray="600" strokeDashoffset={600 * (1 - draw(t, B.hotWallet2, 0.6))} />
          <polygon points="545,1300 512,1268 562,1262" fill={C.red} opacity={draw(t, B.hotWallet2 + 0.5, 0.15)} />
        </svg>
      </AbsoluteFill>

      {/* ---- C: the bank fixed-deposit analogy ---- */}
      <AbsoluteFill style={{opacity: Cp}}>
        {/* bank turns into Binance on "fixed deposit = Binance hot wallet" */}
        <div style={at(540, 720, P('bank'), 1 - draw(t, B.fdIsHot, 0.5))}><Bank w={420} /><Label text="BANK" size={70} style={{marginTop: 4}} /></div>
        <div style={at(540, 720, pop(f, fps, B.fdIsHot), draw(t, B.fdIsHot, 0.5))}><BinanceMark size={300} /><Label text="BINANCE" size={70} color={C.yellow} style={{marginTop: 6}} /></div>
        <div style={at(540, 1180, P('fixedDeposit'))}>
          <Vault w={560} h={260} color={interpolate(t, [B.fdIsHot, B.fdIsHot + 0.5], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) > 0.5 ? C.hot : '#2E7D5B'}>
            <Label text={t < B.fdIsHot + 0.25 ? 'FIXED DEPOSIT' : 'HOT WALLET'} size={62} />
          </Vault>
        </div>
        {/* our money flows in when we buy / sell dollars */}
        {[200, 540, 880].map((x, i) => <div key={i} style={at(x, 1520, pop(f, fps, B.coins + i * 0.1))}><Person size={110} /></div>)}
        {Array.from({length: 9}).map((_, k) => {
          const src = [200, 540, 880][k % 3], st = B.coins + 0.3 + k * 0.38, u = interpolate(t, [st, st + 0.9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return <div key={k} style={at(src + (540 - src) * u, 1440 - 180 * u, u > 0 && u < 1 ? 1 : 0, u > 0 && u < 1 ? 1 : 0)}><Coin size={70} /></div>;
        })}
        <div style={at(540, 1660, draw(t, B.coins, 0.4))}><Label text="Buy / Sell $" size={50} color={C.yellow} /></div>
        <div style={at(540, 1000, draw(t, B.fdIsHot + 0.3, 0.4))}><Label text="=" size={110} color={C.white} /></div>
      </AbsoluteFill>

      {/* ---- D: the attack ---- */}
      <AbsoluteFill style={{opacity: Dp}}>
        <div style={at(540, 760, 1)}><Vault w={520} h={420} color={C.hot}><div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <BinanceMark size={170} /><Label text="HOT WALLET" size={56} style={{marginTop: 8}} /></div></Vault></div>
        <div style={at(190, 520, P('attack', 10))}><Hacker size={240} /></div>
        {Array.from({length: 14}).map((_, k) => {
          const a = (k / 14) * Math.PI * 2, u = interpolate(t, [B.attack + 0.2 + (k % 4) * 0.08, B.attack + 1.4 + (k % 4) * 0.08], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return <div key={k} style={at(540 + Math.cos(a) * 520 * u, 760 + Math.sin(a) * 620 * u, 1, u > 0 && u < 1 ? 1 : 0)}><Coin size={80} /></div>;
        })}
        <div style={at(540, 1330, pop(f, fps, B.stolen, 9))}><Label text="-$6.3 BILLION" size={124} color={C.red}
          style={{WebkitTextStroke: '6px white', paintOrder: 'stroke fill'} as React.CSSProperties} /></div>
        <div style={at(540, 1490, draw(t, B.stolen + 0.3, 0.4))}><Label text="from Binance's hot wallet" size={52} /></div>
      </AbsoluteFill>
      <AbsoluteFill style={{background: C.red, opacity: flash}} />
    </AbsoluteFill>
  );
};
