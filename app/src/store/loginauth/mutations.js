export function loginAuth (state, opened) {
  state.authin = opened
}

export function loginName (state, opened) {
  state.login_name = opened
}

export function loginId (state, opened) {
  state.operator = opened
}

export function accessToken (state, opened) {
  state.access_token = opened
}
