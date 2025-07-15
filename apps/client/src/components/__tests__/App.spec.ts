import { mount } from '@vue/test-utils';
import App from '../../App.vue';

describe('App.vue', () => {
  it('renders the App component', () => {
    const wrapper = mount(App);
    expect(wrapper.vm).toBeTruthy();
  });

  it('mounts without errors', () => {
    expect(() => {
      mount(App);
    }).not.toThrow();
  });
});
