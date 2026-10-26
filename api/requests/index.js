'use strict';
const {getService}=require('../shared/service.cjs');
module.exports=async function(context,req) {
  const result=await getService().requests(req.query);
  context.res={status:result.status,headers:result.headers,body:result.body};
};
