export function displayValue(value) {
  if (value === null || value === undefined || value === '') return 'ثبت نشده';
  if (typeof value === 'boolean') return value ? 'بله' : 'خیر';
  return String(value);
}

export function questionOf(answer) {
  return answer.question || answer.survey_question || {};
}

export function answerValue(answer, type) {
  const question = questionOf(answer);
  if (type === 'Multichoice') {
    return (
      (answer.multichoice || [])
        .map((choice) => {
          const item =
            typeof choice === 'object'
              ? choice
              : (question.answer_choices || []).find((c) => c.id === choice);
          return item ? item.answer : String(choice);
        })
        .join('، ') || 'پاسخ ثبت نشده'
    );
  }
  const field = {
    YesNo: 'bool',
    Triple: 'bool',
    Score: 'score',
    RadioChoice: 'radio',
    DropDownList: 'dropdown',
    Input: 'text',
    Description: 'description',
    Number: 'number',
    Price: 'price',
  }[type];
  const value = answer[field];
  if (type === 'Triple' && value === null) return 'نامشخص';
  if (value === null || value === undefined || value === '') return 'پاسخ ثبت نشده';
  if (type === 'RadioChoice' || type === 'DropDownList') return value.answer || 'پاسخ ثبت نشده';
  if (type === 'Score') return `${value} از ۵`;
  if (type === 'Price') return `${Number(value).toLocaleString('fa-IR')} ریال`;
  return displayValue(value);
}

export function answerDraft(answer = {}) {
  return Object.fromEntries(
    [
      'bool',
      'score',
      'number',
      'price',
      'text',
      'description',
      'radio',
      'dropdown',
      'multichoice',
    ].map((key) => {
      let value = answer[key];
      if (key === 'multichoice')
        value = (value || []).map((c) => (typeof c === 'object' ? c.id : c));
      else if (key === 'radio' || key === 'dropdown')
        value = value && typeof value === 'object' ? value.id : value;
      return [key, value === undefined ? null : value];
    })
  );
}

export function answerPayload(draft, question, recordId, survey) {
  const result = {};
  const fields = {
    YesNo: 'bool',
    Triple: 'bool',
    Score: 'score',
    RadioChoice: 'radio',
    DropDownList: 'dropdown',
    Input: 'text',
    Description: 'description',
    Number: 'number',
    Price: 'price',
    Multichoice: 'multichoice',
  };
  (question.answer_type || []).forEach((type) => {
    const key = fields[type.name];
    if (!key) return;
    let value = draft[key];
    if (['number', 'score', 'price', 'radio', 'dropdown'].includes(key))
      value = value === '' || value === null ? null : Number(value);
    result[key] = value;
  });
  result[survey ? 'survey_question' : 'question'] = question.id;
  result[survey ? 'survey_fill_out' : 'visit'] = Number(recordId);
  return result;
}
