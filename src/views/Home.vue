<template>
  <div id="home" @paste="onPaste">
    <nav class="indigo">
      <div class="nav-wrapper container">
        <ul id="nav-mobile" class="left hide-on-med-and-down" style="width:100%;">
          <li style="width:100%;">
            <div class="input-field inline row" style="width:100%;">
              <span class="col s1">Path:</span>
              <input 
                type="text" 
                @keyup.enter="changePath"
                v-model="queryInput" 
                class="col s11"
                style="color:white;margin-top:8px;"/>
            </div>
          </li>
        </ul>
      </div>
    </nav>
    <div class="container" style="padding-top:10px;">
      <div class="row">
        <div class="col s2">
          <textarea 
            @change="textareaChange"
            style="height:50px;"></textarea>
        </div>
        <div class="col s10"
            style="border:1px dashed; height:50px; line-height:50px;"
            @dragover.prevent
            @drop="onDrop">
          Dropme
        </div>
      </div>
      <div class="row">
        <div class="col s3" v-for="(img, imgid) in imageList" :key="imgid">
          <div class="card" style="float:left;width:100%;">
            <div class="card-image"
                :style="{'height': '200px', 
                         'width': '100%', 
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
                <i style="cursor:pointer;" class="fa fa-eye"></i>
                <i style="cursor:pointer;" class="fa fa-copy"></i>
                <i style="cursor:pointer;" class="fa fa-trash"></i>
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

var baseurl = `http://${window.location.hostname}:9096`
var thumburl = `${baseurl}/thumb/`
export default {
  props: ['query'],
  components: {
    
  },
  data(){
    return {
      queryInput: '',
      imageData: '',
      imageList: [],
      baseurl,
      thumburl
    }
  },
  methods: {
    onPaste: function (e){
      console.log('paste trigger', e)
      let file = e.clipboardData.items[0].getAsFile()
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
      })
    },
    textareaChange: function (e){
      console.log(e)
      let val = e.target.value
      if (val.includes('data:image')){
        this.sendImage64(val)
        e.target.value = ''
      }
    },
    changePath(){
      this.$router.push({path: '/'+this.queryInput})
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
      this.axios.get(baseurl+'/list/'+tquery).then((rs) => {
        this.imageList = rs.data
      })
    }
  },
  created(){
    this.queryInput = this.query
  },
  mounted(){
    this.rebuild_list()
  },
  watch: {
    $route(to, from){
      //console.log('watch', to)
      this.rebuild_list()
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
