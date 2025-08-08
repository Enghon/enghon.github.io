// js.js
const iscream = 'aHR0cDovLzExNC42Ni42MS4xMzE=';

const pig = {
  Fuck2: 'Nzg5MA==',
  Fuck3: 'MTc4NjA=',
  Fuck4: 'Mzg4ODg=',
  Fuck5: 'MjgwOTA=',
  Fuck6: 'NTI2Ng==',
  Fuck7: 'NjY2Mi90cmVlL3dvcms='
};

    function getObscureDatePwd() {
      const d = new Date();
      let mm = d.getMonth() + 1;
      let dd = d.getDate();
      let s = (mm < 10 ? '0' : '') + mm + (dd < 10 ? '0' : '') + dd;
      return obscureEncrypt(s);
    }
