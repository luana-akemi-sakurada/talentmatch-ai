export function modelName(name: string) {
  if (name === 'LogisticRegression') return 'Regressão logística'
  if (name === 'RandomForest' || name === 'RandomForestClassifier') return 'Random Forest'
  if (name.startsWith('MLP')) return 'MLP (rede neural)'
  return name
}

export const percent = (value: number) => `${(value * 100).toFixed(2).replace('.', ',')}%`
export const f1 = (value: number) => value.toFixed(4).replace('.', ',')
