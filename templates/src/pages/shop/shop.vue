<template>
  <q-page class="flex flex-top">
    <template>
      <div class="q-pa-md">
        <div class="q-gutter-y-md" style="max-width: 100%">
          <q-tabs
            v-model="detaillink"
          >
            <transition appear enter-active-class="animated zoomIn">
              <q-route-tab name="shoplist" :label="$t('shop.shop')" icon="perm_contact_calendar" :to="{ name: 'shoplist' }" exact/>
            </transition>
            <transition appear enter-active-class="animated zoomIn">
              <q-route-tab name="shoptype" :label="$t('shoptype.shop_type')" icon="img:statics/staff/stafftype.png" :to="{ name: 'shoptype' }" exact/>
            </transition>
            <transition v-if="$route.name === 'shopwarehouse'" appear enter-active-class="animated zoomIn">
              <q-route-tab name="shopwarehouse" :label="$t('shopwarehouse.shop_warehouse')" icon="img:statics/staff/stafftype.png" :to="{ name: 'shopwarehouse' }" exact/>
            </transition>
          </q-tabs>
        </div>
      </div>
    </template>
    <div :style="{width: '100%', margin: '-10px 10px 0 10px'}">
      <router-view />
    </div>
  </q-page>
</template>

<script>
export default {
  name: 'Pageshop',
  data () {
    return {
      detaillink: 'stafflist',
      shop_id: false
    }
  },
  methods: {
  }
}
</script>
