<template>
  <div id="home">
    <nav class="indigo">
      <div class="nav-wrapper container" style="display:flex;">
          <span class="col s1">Path:</span>
          <div class="input-field inline" style="width:100%;">
            <input
              type="text"
              id="autocomplete-input"
              @keyup.enter="changePath"
              @keyup="inputOnChange"
              autocomplete="off"
              ref="inputPath"
              class="col s11 autocomplete"
              style="color:white;margin-top:8px;"/>
          </div>
      </div>
    </nav>
    <div class="container" style="padding-top:10px;">
      <div class="row">
        <div class="col s2"
            style="display:flex; 
                    flex-direction:row; 
                    align-content: center;
                    align-items: center;
                    justify-content: space-around;
                    height:50px;">
          <i class="fa fa-file-pdf" 
                  style="font-size:30px;cursor:no-drop;"></i>
          <i class="fa fa-file-archive" 
                  style="font-size:30px;cursor:pointer;"
                  @click="downloadZip"></i>
          <i class="material-icons" style="font-size:35px;cursor:no-drop;">slideshow</i>
        </div>
        <div class="col s4"
            style="overflow:hidden;height:50px;"
            >
            <input type="file" ref="file" multiple
              @change="onInputChange"
              style="width:100%;height:50px;"/>
        </div>
        <div class="col s4"
            style="border:1px dashed; height:50px; line-height:50px;"
            @dragover.prevent
            @drop="onDrop">
          Dropme
        </div>
        <div class="col s2">
          <textarea
            v-model="textareaValue"
            style="height:50px;"></textarea>
        </div>
      </div>
      <div class="row">
        <div class="col s3" v-for="(img, imgid) in imageList" :key="imgid">
          <div class="card" style="float:left;width:100%;">
            <div class="card-image"
                @click="onView(img)"
                :style="{'height': '200px',
                         'width': '100%',
                         'cursor': 'pointer',
                         'background-image': 'url('+thumburl+img+')',
                         'background-repeat': 'no-repeat',
                         'background-size': 'contain',
                         'background-position': 'center center'}">
              <!--
                <img :src="thumburl+img" style="height:200px;"/>
                <i class="tiny material-icons">content-copy</i>
            <div class="card-content">
            </div>
              -->
            </div>
            <div class="card-action"
              style="display:flex;flex-direction:row;justify-content:space-around;">
                <i style="cursor:pointer;" class="fa fa-eye"
                    @click="onView(img)"></i>
                <i style="cursor:pointer;" class="fa fa-link"
                      v-clipboard:copy="buildLink(img)"
                      v-clipboard:success="onCopy"></i>
                <i style="cursor:pointer;" class="fab fa-markdown"
                    v-clipboard:copy="buildMarkdown(img)"
                    v-clipboard:success="onCopy"></i>
                <i style="cursor:pointer;" class="fa fa-trash"
                    @click="onDelete(img)"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import HelloWorld from '@/components/HelloWorld.vue'
import M from 'materialize-css'

let wloc = window.location
var baseurl = `${wloc.protocol}//api-${wloc.hostname}`
if (process.env.NODE_ENV == 'development' || process.env.VUE_APP_FORCE_BASE)
  baseurl = process.env.VUE_APP_BASEURL
if (baseurl.includes('codeserver'))
  baseurl = 'http://api-dupi2.localshi.com'
var thumburl = `${baseurl}/thumb/`
var imageurl = `${baseurl}/image/`
export default {
  props: ['query'],
  components: {

  },
  data(){
    return {
      queryInput: '',
      imageData: '',
      textareaValue: '',
      imageList: [],
      baseurl,
      thumburl,
      last_path: ''
    }
  },
  methods: {
    bodyHook(value){
      console.log('body hook trigger', value)
      this.sendImage64(value)
    },
    downloadZip(){
      window.open(baseurl+'/download_zip/'+this.query, '_blank')
    },
    onInputChange(){
      let formData = new FormData();

      for( var i = 0; i < this.$refs.file.files.length; i++ ){
          let file = this.$refs.file.files[i];
          formData.append('files[' + i + ']', file);
      }
      formData.append('path', this.query)
      this.msg('Uploading...')
      this.axios.post(baseurl+'/recv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      }).then((rs) => {
        this.msg('Upload Ok')
        this.rebuild_list()
      }).catch((err) => {
        M.toast({'html': err})
      }).finally(() => {
        this.$refs.file.value = ''
      })
    },
    onCopy(){
      this.msg('Copied Ok')
    },
    buildLink(img){
      let imgurl = imageurl+img
      return imgurl
    },
    buildMarkdown(img){
      let imgurl = imageurl+img
      return `[![](${imgurl})](${imgurl})`
    },
    onView(name){
      window.open(imageurl+name, '_blank')
    },
    onDelete(name){
      console.log('on delete trigger', name)
      let payload = {
        'name': name,
        'path': this.query
      }
      this.axios.post(baseurl+'/del', payload).then((rs) => {
        console.log(rs.data)
        this.rebuild_list()
        this.msg('Delete Ok')
      })
    },
    msg(msg){
      M.toast({html: msg})
    },
    onPaste: function (e){
      return
      console.log('paste trigger', e)
      var pastedData = e.clipboardData.getData('text')
      if (pastedData.includes('http')){
        this.sendImage64(pastedData)
      }
      let file = e.clipboardData.items[0].getAsFile()
      console.log('file', file)
      //let data = URL.createObjectURL(file)
      this.createBase64Image(file, (img) => {
        this.sendImage64(img)
      })
    },
    sendImage64(data64){
      let payload = {
        'image64': data64,
        'path': this.query
      }
      this.axios.post(baseurl+'/recv', payload).then((rs) => {
        console.log(rs.data)
        this.rebuild_list()
        this.msg('Save Ok')
      })
    },
    textareaChange: function (val){
      this.textareaValue = ''
      this.msg('Sending..')
      setTimeout(() => {
        if (val.includes('data:image')){
          this.sendImage64(val)
        }else if (val.includes('http')){
          this.sendImage64(val)
        }
      }, 100)
    },
    setInputValue(value){
      this.$refs.inputPath.value = value
    },
    changePath(){
      let query = this.$refs.inputPath.value
      query = query.trim()
      if (query == ''){
        query = 'all'
        this.setInputValue(query)
      }
      if (query == this.last_path) return
      this.$router.push({path: '/'+query})
    },
    onDrop: function (e){
      e.stopPropagation();
      e.preventDefault();
      var files = e.dataTransfer.files
      this.createBase64Image(files[0], (img) => {
        this.sendImage64(img)
      })
    },
    createBase64Image(fileObject, callback = ()=>{}){
      const reader = new FileReader()
      reader.onload = (e) => {
        this.imageData = e.target.result;
        callback(e.target.result)
      }
      //reader.readAsBinaryString(fileObject)
      reader.readAsDataURL(fileObject)
    },
    rebuild_list(){
      let tquery = this.$route.params.query
      this.setInputValue(tquery)
      this.axios.get(baseurl+'/list/'+tquery).then((rs) => {
        this.last_path = tquery
        this.imageList = rs.data
      })
    },
    inputOnChange(e){
      if (this.last_search == e.target.value) return
      if (e.key == 'ArrowDown' || e.key == 'ArrowUp') return
      if (e.key == 'Enter'){
        this.instance.close()
        return
      }
      this.axios.get(baseurl+'/search/'+btoa(e.target.value)).then((rs) => {
        this.instance.updateData(rs.data)
        this.last_search = e.target.value
        if (!this.instance.isOpen)
          this.instance.open()
      })
    },
    updateAutocomplete(){
      //https://stackoverflow.com/questions/39883425/materialize-autocomplete-with-dynamic-data-in-jquery-ajax
      let obj = this
      document.addEventListener('DOMContentLoaded', function (){
        let elem = obj.$el.querySelector('.autocomplete') 
        console.log(elem)
        obj.instance = M.Autocomplete.init(elem, {
          data: {
            Google: null
          },
          onAutocomplete: (val) => {
            obj.changePath()
          }
        })
        window.instance = obj.instance
      })
      //instances[0].autocomplete({
      //  data: {
      //    Apple: null,
      //    Microsoft: null,
      //    Google: null
      //  }
      //}) 
    },
  },
  created(){
    this.queryInput = this.query
  },
  mounted(){
    window.bodyHook = this.bodyHook
    document.getElementById('home').addEventListener('paste', this.onPaste)
    this.rebuild_list()
    //var elems = document.querySelectorAll('.autocomplete')
    //var instances = M.Autocomplete.init(elems, {
    //  data: {
    //    'all': null,
    //    'meetings/splunk/1': null
    //  }
    //})
    this.updateAutocomplete()
  },
  watch: {
    $route(to, from){
      console.log('watch', to)
      //this.setInputValue(to)
      this.rebuild_list()
    },
    'textareaValue': function (to, from){
      if (to != '')
        this.textareaChange(to)
    }
  }
}
</script>

<style>
#home .input-field input[type=text]:focus {
  border-bottom: 1px solid #003a8c;
  box-shadow: 0 1px 0 0 #002766;
}
</style>
