import { useApp } from '../../state/AppContext.jsx'
import AddScan from './AddScan.jsx'
import AddInput from './AddInput.jsx'
import AddTerms from './AddTerms.jsx'
import AddDone from './AddDone.jsx'

const STEPS = {
  scan: AddScan,
  input: AddInput,
  terms: AddTerms,
  done: AddDone,
}

/** 카드 등록 4단계(스캔 → 입력 → 약관 → 완료)를 addStep 으로 갈아끼웁니다. */
export default function AddCard() {
  const { state } = useApp()
  const Step = STEPS[state.addStep] ?? AddScan
  return <Step />
}
