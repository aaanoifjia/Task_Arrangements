import './PromptField.css'

export type PromptFieldProps = {
  value: string
  onChange: (value: string) => void
}

function PromptField({ value, onChange }: PromptFieldProps) {
  return (
    <label className="prompt-field">
      Prompt
      <textarea
        aria-label="Task prompt"
        rows={12}
        spellCheck={false}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}

export default PromptField
