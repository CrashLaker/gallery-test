module.exports = {
    // options...
    runtimeCompiler: true,
    devServer: {
        disableHostCheck: true,
        watchOptions: {
            poll: true
        },
        public: process.env.BASEURL
    },
}
