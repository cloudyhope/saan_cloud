import store from "@/store/index";
import PersianDate from "persian-date";

function checkUserAccess(action) {
  let userAccess = store.state.userConfig.userAccess;
  return userAccess.includes(action);
}


function toPersianCurrency(value, symbol, decimals, options) {
  let separator;
  let digitsRE = /(\d{3})(?=\d)/g;
  let sign = value < 0 ? "-" : "";
  options = options || {};
  value = parseFloat(value);
  if (!isFinite(value) || (!value && value !== 0)) return "";
  symbol = symbol != null ? sign + " " + symbol : sign + " " + "تومان";
  decimals = decimals != null ? decimals : 2;
  separator = options.separator != null ? options.separator : ",";
  let stringified = Math.abs(value).toFixed(decimals);
  stringified = options.decimalSeparator
    ? stringified.replace(".", options.decimalSeparator)
    : stringified;
  let _int = decimals ? stringified.slice(0, -1 - decimals) : stringified;
  let i = _int.length % 3;
  let head = i > 0 ? _int.slice(0, i) + (_int.length > 3 ? separator : "") : "";
  let _float = decimals ? stringified.slice(-1 - decimals) : "";
  symbol =
    "‫‫" +
    head +
    _int.slice(i).replace(digitsRE, "$1" + separator) +
    _float +
    symbol;
  return symbol;
}

function validateList(validationRules, arrayLength, name) {
  let errorsArray = [];

  // check for required
  if (validationRules.required && !arrayLength) {
    errorsArray.push(`${name} اجباری است`);
  }

  // check for length
  if (validationRules.length && arrayLength !== validationRules.length) {
    errorsArray.push(`تعداد فلان باید ${validationRules.length} باشد `);
  }

  // check for max length
  if (validationRules.maxLength && arrayLength >= validationRules.maxLength) {
    errorsArray.push(
      `تعداد ${name} باید کمتر از ${validationRules.maxLength} باشد `
    );
  }

  // check for min length
  if (validationRules.minLength && arrayLength <= validationRules.minLength) {
    errorsArray.push(
      `تعداد ${name} باید بیشتر از ${validationRules.minLength} باشد `
    );
  }

  return errorsArray;
}

// {
//   "data": {
//   "maps": [
//     {
//       "module.page.field": "rule1"
//     },
//     {
//       "module.page.field2": "rule2"
//     }
//   ],
//       "rules": [
//     {
//       "key": "rule1",
//       "required": false,
//       "minLength": 0,
//       "maxLength": 0
//     },
//     {
//       "key": "rule2",
//       "required": false,
//       "minLength": 0,
//       "maxLength": 0
//     }
//   ]
// },
//   "code": 200
// }

function ruleGetter(pageName, fieldName) {
  const mapKey = pageName + "_" + fieldName;

  let ruleKey = undefined;
  store.state.userConfig.validationRules.maps.some((item) => {
    if (item.path.toLowerCase() == mapKey.toLowerCase()) {
      ruleKey = item.key;
      return true;
    }
  });

  return store.state.userConfig.validationRules.rules.find((item) => {
    if (item.key === ruleKey) {
      return item;
    }
  });
}

function convertUnixTimestampToDate(timestamp, format = "YY/MM/D") {
  const time = new PersianDate(timestamp).format(format);
  return time;
}

function setDefaultItem(defaultArray, item, optionalKey) {
  return defaultArray.find((i) => i[optionalKey] == item);
}

function deleteUnnecessaryProperties (object, clone = true) {
  if (clone) {
    object = object instanceof Array
      ? [ ...object ]
      : { ...object }
  }

  for (const key in object) {
    if (typeof object[key] === 'object') {
      if (clone) {
        object[key] = object[key] instanceof Array
          ? [ ...object[key] ]
          : { ...object[key] }
      }

      deleteUnnecessaryProperties(object[key], false)
    }

    if (
      object[key] === undefined ||
      object[key] === null ||
      object[key] === '' ||
      Number.isNaN(object[key]) ||
      (
        typeof object[key] === 'object' &&
        !Object.keys(object[key]).length
      )
    ) {
      if (object instanceof Array) object.splice(key, 1)
      else delete object[key]
    }
  }

  return object
}

function sequentialIDGenerator () {
  let id = 0

  return () => id++
}

export default {
  toPersianCurrency,
  checkUserAccess,
  validateList,
  ruleGetter,
  convertUnixTimestampToDate,
  setDefaultItem,
  deleteUnnecessaryProperties,
  sequentialIDGenerator
};
