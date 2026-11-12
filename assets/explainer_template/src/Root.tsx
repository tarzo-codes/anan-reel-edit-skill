import React from 'react';
import {Composition} from 'remotion';
import {Explainer} from './Explainer';
import beats from '../beats.json';

// Reel 5 v2: Binance hot/cold wallet + bank fixed-deposit explainer. 1080x1920 design space, rendered at scale 2
// (2160x3840) so it drops onto the reel at 100%. Timing comes from beats.json (word timestamps, written by plan_r5v2.py).
export const Root: React.FC = () => (
  <Composition id="explainer" component={Explainer} width={1080} height={1920} fps={25}
    durationInFrames={Math.round(beats.duration * 25)} defaultProps={{}} />
);
